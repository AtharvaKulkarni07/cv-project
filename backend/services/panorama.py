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
    Returns (src_pts, dst_pts, match_visualisation).
    """
    sift = cv2.SIFT_create()
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    kp1, des1 = sift.detectAndCompute(gray1, None)
    kp2, des2 = sift.detectAndCompute(gray2, None)

    # BF kNN match + ratio test
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    good = [m for m, n in matches if m.distance < 0.75 * n.distance]

    # Visualise
    match_img = cv2.drawMatches(
        img1, kp1, img2, kp2, good, None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    return src_pts, dst_pts, match_img, len(good)


# ── RANSAC Homography ───────────────────────────────────────────────

def ransac_homography(
    src_pts: np.ndarray,
    dst_pts: np.ndarray,
    iterations: int = 2000,
    threshold: float = 4.0,
) -> tuple[np.ndarray, int]:
    """Custom RANSAC loop to find the best homography. Returns (H, inlier_count)."""
    best_H = None
    max_inliers = 0

    for _ in range(iterations):
        idx = np.random.choice(len(src_pts), 4, replace=False)
        H, _ = cv2.findHomography(src_pts[idx], dst_pts[idx], cv2.RANSAC, threshold)
        if H is None:
            continue

        transformed = cv2.perspectiveTransform(src_pts, H)
        dists = np.linalg.norm(transformed - dst_pts, axis=2)
        inliers = int(np.sum(dists < threshold))

        if inliers > max_inliers:
            max_inliers = inliers
            best_H = H

    return best_H, max_inliers


# ── Image Stitching (Warp + Composite) ──────────────────────────────

def stitch_images(img1: np.ndarray, img2: np.ndarray, H: np.ndarray) -> np.ndarray:
    """Warp img1 into img2's frame via H, then composite."""
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]

    # Transform corners of img1
    pts = np.float32([[0, 0], [0, h1], [w1, h1], [w1, 0]]).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(pts, H)

    x_min, x_max = int(np.min(transformed[:, 0, 0])), int(np.max(transformed[:, 0, 0]))
    y_min, y_max = int(np.min(transformed[:, 0, 1])), int(np.max(transformed[:, 0, 1]))

    tx = -x_min if x_min < 0 else 0
    ty = -y_min if y_min < 0 else 0

    out_w = max(x_max - x_min, w2 + tx)
    out_h = max(y_max - y_min, h2 + ty)

    # Translation matrix so nothing goes negative
    T = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]], dtype=np.float64)
    warped = cv2.warpPerspective(img1, T @ H, (out_w, out_h))

    # Place img2 into canvas
    y_start, y_end = max(ty, 0), min(ty + h2, out_h)
    x_start, x_end = max(tx, 0), min(tx + w2, out_w)
    roi_y1, roi_x1 = max(-ty, 0), max(-tx, 0)
    roi_y2 = roi_y1 + (y_end - y_start)
    roi_x2 = roi_x1 + (x_end - x_start)

    mask = warped[y_start:y_end, x_start:x_end].sum(axis=2) == 0
    warped[y_start:y_end, x_start:x_end][mask] = img2[roi_y1:roi_y2, roi_x1:roi_x2][mask]

    return warped


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

        # Step 3 — RANSAC homography
        H, inlier_count = ransac_homography(src_pts, dst_pts, threshold=0.5)
        if H is None:
            raise RuntimeError(f"Homography estimation failed for pair {i}")
        yield {
            "step": 3,
            "name": "RANSAC Homography",
            "algorithm": "RANSAC (2000 iters)",
            "description": f"Estimated homography with {inlier_count} inliers.",
            "images": [],
            "metadata": {
                "inliers": inlier_count,
                "iterations": 2000,
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
            "algorithm": "Perspective Warp",
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
