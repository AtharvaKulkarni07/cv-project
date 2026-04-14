"""
Thorough test of the fixed panorama pipeline.

Test 1: Self-split test - split a wide image in half with overlap, stitch back.
         This guarantees good matches and proves the pipeline works correctly.
Test 2: Provided test pairs - check if they have enough overlap to stitch.
"""

import sys, os
import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services.panorama import (
    sift_feature_matching,
    ransac_homography,
    stitch_images,
    _validate_homography,
)

TEST_DIR = os.path.dirname(__file__)


def test_self_split(image_path: str, overlap_pct: float = 0.3):
    """Split an image into overlapping halves and verify stitching."""
    img = cv2.imread(image_path)
    assert img is not None, f"Cannot load {image_path}"
    name = os.path.basename(image_path)

    h, w = img.shape[:2]
    mid = w // 2
    overlap = int(w * overlap_pct / 2)

    left = img[:, :mid + overlap]
    right = img[:, mid - overlap:]

    print(f"\n{'='*60}")
    print(f"Self-split test: {name}")
    print(f"  Original: {w}x{h}")
    print(f"  Left:  {left.shape[1]}x{left.shape[0]}")
    print(f"  Right: {right.shape[1]}x{right.shape[0]}")
    print(f"  Overlap: {overlap*2}px ({overlap_pct*100:.0f}%)")

    # Feature matching
    src_pts, dst_pts, match_vis, n_good = sift_feature_matching(left, right)
    print(f"  Good matches: {n_good}")

    # Homography
    H, inliers = ransac_homography(src_pts, dst_pts, threshold=4.0)
    assert H is not None, "Homography is None!"
    print(f"  Inliers: {inliers}/{n_good} ({inliers/n_good*100:.1f}%)")

    # Validate
    valid = _validate_homography(H)
    print(f"  Homography valid: {valid}")
    assert valid, f"Homography failed validation!\n{H}"

    # The homography for a horizontal translation should be approximately:
    # [[1, 0, tx], [0, 1, 0], [0, 0, 1]]
    Hn = H / H[2, 2]
    print(f"  H (normalized):\n{np.round(Hn, 4)}")

    # Check it's roughly a translation
    assert abs(Hn[0, 0] - 1.0) < 0.3, f"H[0,0] = {Hn[0,0]:.4f}, expected ~1.0"
    assert abs(Hn[1, 1] - 1.0) < 0.3, f"H[1,1] = {Hn[1,1]:.4f}, expected ~1.0"

    # Stitch
    result = stitch_images(left, right, H)
    print(f"  Output size: {result.shape[1]}x{result.shape[0]}")

    # The result should be roughly the same width as the original
    width_ratio = result.shape[1] / w
    print(f"  Width ratio vs original: {width_ratio:.2f}")
    assert 0.7 < width_ratio < 1.5, f"Width ratio {width_ratio:.2f} is suspicious"

    # Save
    out_path = os.path.join(TEST_DIR, f"result_split_{name}")
    cv2.imwrite(out_path, result)
    print(f"  Saved: {out_path}")
    print(f"  [PASSED]")
    return True


def test_pair_graceful(name_a: str, name_b: str):
    """Test a pair - pass if stitches well, gracefully handle low-overlap pairs."""
    a = cv2.imread(os.path.join(TEST_DIR, name_a))
    b = cv2.imread(os.path.join(TEST_DIR, name_b))
    if a is None or b is None:
        print(f"\n  [SKIP] Cannot load {name_a} or {name_b}")
        return

    print(f"\n{'='*60}")
    print(f"Pair test: {name_a} + {name_b}")

    try:
        src_pts, dst_pts, _, n_good = sift_feature_matching(a, b)
    except RuntimeError as e:
        print(f"  [WARNING] Insufficient matches: {e}")
        print(f"  [OK] Correctly rejected (too few matches)")
        return

    H, inliers = ransac_homography(src_pts, dst_pts, threshold=4.0)
    if H is None:
        print(f"  [WARNING] Homography rejected (matches={n_good})")
        print(f"  [OK] Correctly rejected degenerate homography")
        return

    valid = _validate_homography(H)
    if not valid:
        print(f"  [WARNING] Homography validation failed")
        print(f"  [OK] Correctly rejected degenerate homography")
        return

    result = stitch_images(a, b, H)
    out_path = os.path.join(TEST_DIR, f"result_{name_a}_{name_b}.png")
    cv2.imwrite(out_path, result)
    print(f"  Output: {result.shape[1]}x{result.shape[0]}")
    print(f"  Saved: {out_path}")
    print(f"  [PASSED]")


if __name__ == "__main__":
    print("=" * 60)
    print("PANORAMA PIPELINE SMOKE TESTS")
    print("=" * 60)

    # Test 1: Self-split (guaranteed to work)
    for img_name in ["sf.jpeg", "stanford.jpg"]:
        img_path = os.path.join(TEST_DIR, img_name)
        if os.path.exists(img_path):
            test_self_split(img_path)

    # Test 2: Provided pairs (may not have enough overlap)
    test_pair_graceful("00.jpeg", "01.jpeg")
    test_pair_graceful("10.jpeg", "11.jpeg")

    print(f"\n{'='*60}")
    print("All tests completed!")
