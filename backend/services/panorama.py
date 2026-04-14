"""
Panorama stitching pipeline — migrated from panorama-1.py.

Steps:
  0  Image Load         — decode & save uploaded images
  1  Harris Corners     — custom corner detection
  2  SIFT Matching      — feature extraction + BFMatcher
  3  RANSAC Homography  — robust homography estimation
  4  Warping & Stitch   — perspective warp + compositing
"""

import cv2
import numpy as np
from typing import Generator

from services.image_utils import save_image


# -- Step helpers yielded as dicts for SSE streaming --

StepDict = dict  # shorthand


# ── Harris Corner Detection ─────────────────────────────────────────

def _apply_gaussian_blur(image: np.ndarray, ksize: int) -> np.ndarray:
    """Smooth image with a Gaussian kernel."""
    return cv2.GaussianBlur(image, (ksize, ksize), 0)


def _compute_gradients(image: np.ndarray):
    """Sobel gradients in x and y."""
    Ix = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    Iy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    return Ix, Iy


def _compute_harris_response(Ix, Iy, alpha: float, win: int) -> np.ndarray:
    """Harris corner response matrix R."""
    Ixx, Ixy, Iyy = Ix ** 2, Ix * Iy, Iy ** 2
    kernel = np.ones((win, win), dtype=np.float32)
    Sxx = cv2.filter2D(Ixx, -1, kernel)
    Sxy = cv2.filter2D(Ixy, -1, kernel)
    Syy = cv2.filter2D(Iyy, -1, kernel)
    det = (Sxx * Syy) - (Sxy ** 2)
    trace = Sxx + Syy
    return det - alpha * (trace ** 2)


def _identify_corners(R: np.ndarray, threshold: float) -> np.ndarray:
    """Threshold the response matrix into a binary corner map."""
    corners = np.zeros_like(R, dtype=np.uint8)
    corners[R > threshold * np.max(R)] = 255
    return corners


def _non_maximal_suppression(corners: np.ndarray, win: int) -> np.ndarray:
    """Suppress non-maximal corners in a local window."""
    half = win // 2
    out = corners.copy()
    for i in range(half, corners.shape[0] - half):
        for j in range(half, corners.shape[1] - half):
            if corners[i, j] == 255:
                patch = corners[i - half:i + half + 1, j - half:j + half + 1]
                if np.max(patch) != 255:
                    out[i, j] = 0
    return out


def _draw_corners(image: np.ndarray, corners: np.ndarray, offset: int) -> np.ndarray:
    """Draw red circles on corner locations."""
    vis = image.copy()
    h, w = vis.shape[:2]
    for y in range(offset, h - offset):
        for x in range(offset, w - offset):
            if corners[y, x] == 255:
                cv2.circle(vis, (x, y), 5, (0, 0, 255), -1)
    return vis


def harris_corner_detector(
    image: np.ndarray,
    gauss_k: int = 3,
    alpha: float = 0.04,
    threshold: float = 0.30,
    nhood: int = 5,
    nms: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Full Harris pipeline on a BGR image. Returns (visualisation, corner_map)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    smooth = _apply_gaussian_blur(gray, gauss_k)
    Ix, Iy = _compute_gradients(smooth)
    R = _compute_harris_response(Ix, Iy, alpha, nhood)
    corners = _identify_corners(R, threshold)
    if nms:
        corners = _non_maximal_suppression(corners, nhood)
    vis = _draw_corners(image, corners, nhood // 2)
    return vis, corners


# ── SIFT Feature Matching ───────────────────────────────────────────

def sift_feature_matching(img1: np.ndarray, img2: np.ndarray):
    """
    SIFT detect + BFMatcher with Lowe's ratio test.
    Returns (src_pts, dst_pts, match_visualisation, n_good).
    """
    sift = cv2.SIFT_create()
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
        raise RuntimeError(
            "Insufficient keypoints detected. Ensure images have enough "
            "texture and overlap."
        )

    # BF kNN match + Lowe's ratio test
    bf = cv2.BFMatcher(cv2.NORM_L2)
    matches = bf.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]

    if len(good) < 4:
        raise RuntimeError(
            f"Only {len(good)} good matches found (need >= 4). "
            "Images may not overlap sufficiently."
        )

    # Visualise
    match_img = cv2.drawMatches(
        img1, kp1, img2, kp2, good, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    return src_pts, dst_pts, match_img, len(good)


# ── RANSAC Homography ───────────────────────────────────────────────

def _validate_homography(H: np.ndarray) -> bool:
    """
    Lightweight sanity-check for a 3×3 homography matrix.

    Only rejects truly catastrophic / degenerate transforms:
      - Non-finite values
      - Near-singular matrix (determinant close to zero)
      - Negative determinant (orientation flip — usually wrong)

    We deliberately keep this lenient because OpenCV's RANSAC with a
    high inlier ratio is already the best quality signal.  Overly
    strict checks on perspective coefficients or condition numbers
    reject valid panorama homographies from real cameras.
    """
    if H is None or H.shape != (3, 3):
        return False

    # Must be finite
    if not np.isfinite(H).all():
        return False

    # Normalize so H[2,2] == 1 to make checks meaningful
    if abs(H[2, 2]) < 1e-8:
        return False
    Hn = H / H[2, 2]

    # Check determinant — must be positive (no reflection) and not
    # near-zero (the original bug had det ≈ 0.001).
    det = np.linalg.det(Hn)
    if det < 0.05 or det > 50.0:
        return False

    # Check that scale components are not wildly off
    sx = np.sqrt(Hn[0, 0] ** 2 + Hn[1, 0] ** 2)
    sy = np.sqrt(Hn[0, 1] ** 2 + Hn[1, 1] ** 2)
    if sx < 0.1 or sx > 10.0 or sy < 0.1 or sy > 10.0:
        return False

    return True


def ransac_homography(
    src_pts: np.ndarray,
    dst_pts: np.ndarray,
    threshold: float = 5.0,
) -> tuple[np.ndarray | None, int]:
    """
    Compute a robust homography using OpenCV's built-in RANSAC on ALL
    matched points.

    The previous implementation ran cv2.findHomography (with RANSAC) on
    random 4-point subsets in a manual loop — this is redundant and
    numerically fragile.  OpenCV's internal RANSAC already handles
    random sampling, inlier counting, and re-estimation.

    Returns (H, inlier_count).
    """
    n_pts = len(src_pts)
    if n_pts < 4:
        return None, 0

    # Let OpenCV handle the full RANSAC pipeline on all points
    H, mask = cv2.findHomography(
        src_pts, dst_pts,
        method=cv2.RANSAC,
        ransacReprojThreshold=threshold,
        maxIters=5000,
        confidence=0.999,
    )

    if H is None or mask is None:
        return None, 0

    inlier_count = int(mask.sum())
    inlier_ratio = inlier_count / n_pts

    # Primary quality gate: inlier ratio.
    # A good homography should have a substantial fraction of inliers.
    # If less than 25% of matches are inliers the geometry is suspect.
    min_inliers = max(8, int(0.25 * n_pts))
    if inlier_count < min_inliers:
        return None, 0

    # Secondary gate: catch truly degenerate matrices
    if not _validate_homography(H):
        # Fallback: re-estimate with only inlier points using LMEDS
        inlier_mask = mask.ravel().astype(bool)
        if inlier_mask.sum() >= 4:
            H_refined, mask2 = cv2.findHomography(
                src_pts[inlier_mask],
                dst_pts[inlier_mask],
                method=cv2.LMEDS,
            )
            if H_refined is not None and _validate_homography(H_refined):
                H = H_refined
                inlier_count = int(mask2.sum()) if mask2 is not None else inlier_count
            else:
                return None, 0
        else:
            return None, 0

    return H, inlier_count


# ── Image Stitching (Warp + Composite) ──────────────────────────────

def stitch_images(img1: np.ndarray, img2: np.ndarray, H: np.ndarray) -> np.ndarray:
    """
    Warp img1 into img2's frame via H, then composite with linear
    alpha-blending in overlapping regions to avoid hard seams.
    """
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    # Transform corners of img1 to find output canvas bounds
    corners_img1 = np.float32(
        [[0, 0], [0, h1], [w1, h1], [w1, 0]]
    ).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(corners_img1, H)

    # Also include corners of img2 (at their original positions)
    corners_img2 = np.float32(
        [[0, 0], [0, h2], [w2, h2], [w2, 0]]
    ).reshape(-1, 1, 2)

    all_corners = np.concatenate([transformed, corners_img2], axis=0)

    x_min = int(np.floor(np.min(all_corners[:, 0, 0])))
    x_max = int(np.ceil(np.max(all_corners[:, 0, 0])))
    y_min = int(np.floor(np.min(all_corners[:, 0, 1])))
    y_max = int(np.ceil(np.max(all_corners[:, 0, 1])))

    # Translation to shift everything into positive coordinates
    tx = -x_min if x_min < 0 else 0
    ty = -y_min if y_min < 0 else 0

    out_w = x_max - x_min
    out_h = y_max - y_min

    # Clamp canvas size to prevent memory explosion from bad warps
    max_dim = max(w1, w2, h1, h2) * 4
    if out_w > max_dim or out_h > max_dim:
        raise RuntimeError(
            f"Output canvas too large ({out_w}×{out_h}). "
            "Homography may be degenerate."
        )

    # Translation matrix so nothing goes to negative coordinates
    T = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], dtype=np.float64)

    # Warp img1 into the output canvas
    warped1 = cv2.warpPerspective(img1, T @ H, (out_w, out_h))

    # Place img2 into its own canvas at the correct position
    canvas2 = np.zeros((out_h, out_w, 3), dtype=img2.dtype)
    y_off, x_off = ty, tx
    # Compute safe ROI boundaries
    y1_start = max(y_off, 0)
    y1_end = min(y_off + h2, out_h)
    x1_start = max(x_off, 0)
    x1_end = min(x_off + w2, out_w)
    # Corresponding region in img2
    src_y_start = max(-y_off, 0)
    src_y_end = src_y_start + (y1_end - y1_start)
    src_x_start = max(-x_off, 0)
    src_x_end = src_x_start + (x1_end - x1_start)

    canvas2[y1_start:y1_end, x1_start:x1_end] = img2[
        src_y_start:src_y_end, src_x_start:src_x_end
    ]

    # Build binary masks for each image
    mask1 = (warped1.sum(axis=2) > 0).astype(np.float32)
    mask2 = (canvas2.sum(axis=2) > 0).astype(np.float32)

    # Overlap region
    overlap = (mask1 * mask2) > 0

    # Compute distance transforms for smooth blending in the overlap
    # Distance from the edge of each mask → higher weight in the centre
    dist1 = cv2.distanceTransform((mask1 > 0).astype(np.uint8), cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform((mask2 > 0).astype(np.uint8), cv2.DIST_L2, 5)

    # Avoid division by zero
    sum_dist = dist1 + dist2
    sum_dist[sum_dist == 0] = 1.0

    # Alpha weight for img1's contribution
    alpha1 = dist1 / sum_dist
    alpha2 = dist2 / sum_dist

    # Expand to 3 channels
    alpha1_3 = np.stack([alpha1] * 3, axis=-1)
    alpha2_3 = np.stack([alpha2] * 3, axis=-1)

    # Composite: blend in overlap, use original elsewhere
    result = np.zeros((out_h, out_w, 3), dtype=np.float64)

    # Non-overlap: take whichever image is present
    only1 = (mask1 > 0) & (~overlap)
    only2 = (mask2 > 0) & (~overlap)
    result[only1] = warped1[only1].astype(np.float64)
    result[only2] = canvas2[only2].astype(np.float64)

    # Overlap: weighted blend
    result[overlap] = (
        alpha1_3[overlap] * warped1[overlap].astype(np.float64)
        + alpha2_3[overlap] * canvas2[overlap].astype(np.float64)
    )

    return np.clip(result, 0, 255).astype(np.uint8)


# ── Full Pipeline Generator (yields SSE step dicts) ─────────────────

def run_pipeline(images: list[np.ndarray], session_id: str) -> Generator[StepDict, None, None]:
    """
    Run the full panorama pipeline across N images.
    Yields one dict per step for SSE streaming.
    """
    if len(images) < 2:
        raise ValueError("Need at least 2 images")

    # Step 0 — Image load
    load_urls = [save_image(img, session_id, f"input_{i}") for i, img in enumerate(images)]
    yield {
        "step": 0,
        "name": "Image Load",
        "description": f"Loaded {len(images)} input images.",
        "images": load_urls,
        "metadata": {
            "count": len(images),
            "resolutions": [f"{img.shape[1]}×{img.shape[0]}" for img in images],
        },
        "session_id": session_id,
    }

    # Iteratively stitch pairs left-to-right
    result = images[0]

    for i in range(1, len(images)):
        img_left = result
        img_right = images[i]

        # Step 1 — Harris corners
        vis_left, _ = harris_corner_detector(img_left)
        vis_right, _ = harris_corner_detector(img_right)
        urls = [
            save_image(vis_left, session_id, f"harris_left_{i}"),
            save_image(vis_right, session_id, f"harris_right_{i}"),
        ]
        yield {
            "step": 1,
            "name": "Harris Corner Detection",
            "algorithm": "Harris + NMS",
            "description": f"Detected corners on pair {i}/{len(images)-1}.",
            "images": urls,
            "metadata": {"pair": f"{i}/{len(images)-1}", "threshold": 0.30},
            "session_id": session_id,
        }

        # Step 2 — SIFT matching
        src_pts, dst_pts, match_vis, n_good = sift_feature_matching(img_left, img_right)
        match_url = save_image(match_vis, session_id, f"matches_{i}")
        yield {
            "step": 2,
            "name": "Feature Matching",
            "algorithm": "SIFT + BFMatcher",
            "description": f"Found {n_good} good matches after Lowe's ratio test.",
            "images": [match_url],
            "metadata": {"good_matches": n_good, "ratio_threshold": 0.75},
            "session_id": session_id,
        }

        # Step 3 — RANSAC homography (using robust OpenCV RANSAC)
        H, inlier_count = ransac_homography(src_pts, dst_pts)
        if H is None:
            raise RuntimeError(
                f"Homography estimation failed for pair {i}. "
                f"The computed transform was degenerate or had too few inliers."
            )
        yield {
            "step": 3,
            "name": "RANSAC Homography",
            "algorithm": "OpenCV RANSAC (5000 iters, 99.9% conf)",
            "description": f"Estimated homography with {inlier_count} inliers.",
            "images": [],
            "metadata": {
                "inliers": inlier_count,
                "total_matches": n_good,
                "inlier_ratio": round(inlier_count / max(n_good, 1), 3),
                "homography": H.tolist(),
            },
            "session_id": session_id,
        }

        # Step 4 — Warp & stitch
        result = stitch_images(img_left, img_right, H)
        stitch_url = save_image(result, session_id, f"stitch_{i}")
        yield {
            "step": 4,
            "name": "Warping & Stitching",
            "algorithm": "Perspective Warp + Distance-Weighted Blend",
            "description": f"Stitched pair {i}/{len(images)-1} into panorama.",
            "images": [stitch_url],
            "metadata": {
                "output_size": f"{result.shape[1]}×{result.shape[0]}",
                "pair": f"{i}/{len(images)-1}",
            },
            "session_id": session_id,
        }

    # Final panorama URL is the last stitch
    final_url = save_image(result, session_id, "final_panorama")
    yield {
        "event": "complete",
        "final_panorama": final_url,
        "elapsed_seconds": 0,  # filled by the router
        "session_id": session_id,
    }
