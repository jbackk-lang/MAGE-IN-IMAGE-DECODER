"""real_contour_curvature_casia2.py -- test glowny na realnym podzbiorze
CASIA v2 (splicing/copy-move ground truth). Patrz
PREREG_CONTOUR_CURVATURE_v0.1.md + PREREG_CONTOUR_CURVATURE_v0.1_ADDENDUM.md
dla pelnej, zamrozonej specyfikacji -- uruchamiane DOPIERO po przejsciu
bramki syntetycznej w test_contour_curvature.py.
"""
from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np
from scipy.stats import mannwhitneyu

from contour_curvature import compute_reference_threshold, region_kappa_density

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "casia2_splicing_sample")
PATCH = 48
N_BOUNDARY = 40
N_BG = 40
MIN_DIST = 60
N_COMPARISONS = 4
ALPHA_CORR = 0.05 / N_COMPARISONS

IMAGES = [
    ("Tp_D_CRN_M_N_pla00035_pla00033_10997", "splicing"),
    ("Tp_D_CRN_S_N_nat00033_cha00086_11502", "splicing"),
    ("Tp_S_NNN_S_O_pla00077_pla00077_11212", "copy-move"),
    ("Tp_S_NRN_S_N_pla00005_pla00005_10937", "copy-move"),
]


@dataclass
class ImageResult:
    name: str
    kind: str
    n_boundary: int
    n_bg: int
    mean_boundary: float
    mean_bg: float
    p_value: float
    significant: bool


def _load(name: str) -> Tuple[np.ndarray, np.ndarray]:
    gray = cv2.imread(os.path.join(DATA_DIR, f"{name}.jpg"), cv2.IMREAD_GRAYSCALE)
    mask = cv2.imread(os.path.join(DATA_DIR, f"{name}_gt.png"), cv2.IMREAD_GRAYSCALE)
    if gray is None or mask is None:
        raise FileNotFoundError(f"brak pliku dla {name} w {DATA_DIR}")
    mask_bin = (mask > 127).astype(np.uint8)
    return gray, mask_bin


def _boundary_points(mask_bin: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask_bin * 255, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        return np.zeros((0, 2), dtype=np.int64)
    pts = np.concatenate([c.reshape(-1, 2) for c in contours], axis=0)
    return pts  # (x, y)


def _dist_to_mask(mask_bin: np.ndarray) -> np.ndarray:
    inv = (1 - mask_bin).astype(np.uint8)
    # odleglosc kazdego piksela od najblizszego piksela maski (odleglosc do
    # tla maski liczona na dopelnieniu -> distanceTransform na tle wzgledem
    # obiektu daje odleglosc do najblizszego piksela ROWNEGO 0 w wejsciu;
    # chcemy odleglosc do najblizszego piksela maski==1, wiec transformujemy
    # dopelnienie maski.
    return cv2.distanceTransform(inv, cv2.DIST_L2, 5)


def _sample_patches(rng: np.random.Generator, h: int, w: int, half: int,
                     candidates_xy: np.ndarray, n: int) -> List[Tuple[int, int, int, int]]:
    """Zwraca do n ROI (x0,y0,x1,y1) wysrodkowanych na losowo wybranych
    punktach z candidates_xy, przycietych do granic obrazu."""
    if len(candidates_xy) == 0:
        return []
    idx = rng.choice(len(candidates_xy), size=min(n, len(candidates_xy) * 4), replace=True)
    rois = []
    seen = set()
    for i in idx:
        x, y = candidates_xy[i]
        x0, y0 = max(0, x - half), max(0, y - half)
        x1, y1 = min(w, x + half), min(h, y + half)
        if x1 - x0 < 2 * half - 4 or y1 - y0 < 2 * half - 4:
            continue
        key = (x0, y0)
        if key in seen:
            continue
        seen.add(key)
        rois.append((x0, y0, x1, y1))
        if len(rois) >= n:
            break
    return rois


def run_one(name: str, kind: str, seed: int) -> ImageResult:
    gray, mask_bin = _load(name)
    h, w = gray.shape
    half = PATCH // 2

    boundary_xy = _boundary_points(mask_bin)
    dist = _dist_to_mask(mask_bin)
    bg_mask = dist > MIN_DIST
    bg_ys, bg_xs = np.where(bg_mask)
    bg_xy = np.stack([bg_xs, bg_ys], axis=1)

    rng = np.random.default_rng(seed)
    boundary_rois = _sample_patches(rng, h, w, half, boundary_xy, N_BOUNDARY)
    bg_rois = _sample_patches(rng, h, w, half, bg_xy, N_BG)

    bg_grays = [gray[y0:y1, x0:x1] for (x0, y0, x1, y1) in bg_rois]
    threshold = compute_reference_threshold(bg_grays)

    d_boundary = [region_kappa_density(gray, threshold, roi=r) for r in boundary_rois]
    d_bg = [region_kappa_density(gray, threshold, roi=r) for r in bg_rois]
    d_boundary = [d for d in d_boundary if not np.isnan(d)]
    d_bg = [d for d in d_bg if not np.isnan(d)]

    if len(d_boundary) < 5 or len(d_bg) < 5:
        return ImageResult(name, kind, len(d_boundary), len(d_bg),
                            float(np.mean(d_boundary)) if d_boundary else float("nan"),
                            float(np.mean(d_bg)) if d_bg else float("nan"),
                            float("nan"), False)

    stat, p = mannwhitneyu(d_boundary, d_bg, alternative="greater")
    return ImageResult(name, kind, len(d_boundary), len(d_bg),
                        float(np.mean(d_boundary)), float(np.mean(d_bg)),
                        float(p), bool(p < ALPHA_CORR))


def run_real_test(verbose: bool = True) -> List[ImageResult]:
    results = []
    for i, (name, kind) in enumerate(IMAGES):
        res = run_one(name, kind, seed=1000 + i)
        results.append(res)
        if verbose:
            print(f"{name} ({kind}): n_boundary={res.n_boundary} n_bg={res.n_bg} "
                  f"mean_boundary={res.mean_boundary:.4f} mean_bg={res.mean_bg:.4f} "
                  f"p={res.p_value:.4g} significant(Bonferroni)={res.significant}")
    return results


if __name__ == "__main__":
    run_real_test()
