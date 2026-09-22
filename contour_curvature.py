"""contour_curvature.py -- G-branch: dyskretna krzywizna konturow 2D.

Patrz PREREG_CONTOUR_CURVATURE_v0.1.md dla pelnej, zamrozonej specyfikacji.
NIE jest zwiazane z operatorem Weingartena (siatki 3D,
TIMDR-Geometry-Formalism/timdr_geometry/weingarten.py) -- to osobny,
znacznie prostszy klasyczny wzor na krzywizne krzywej plaskiej (kat zmiany
kierunku na jednostke dlugosci luku), zastosowany do konturow wykrytych
przez cv2.Canny + cv2.findContours. Rowniez NIE jest zwiazane z
`detect_twist()` w i2d_core.py (to lokalna asymetria jasnosci bloku
pikseli, zupelnie inny sygnal).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

CANNY_LOW = 50
CANNY_HIGH = 150
CURVATURE_STEP = 3
MIN_CONTOUR_LEN = 20
MAD_TO_STD = 1.4826
K_ROBUST = 3.0


def extract_contours(gray: np.ndarray, low: int = CANNY_LOW, high: int = CANNY_HIGH) -> List[np.ndarray]:
    """Canny + findContours. Zwraca liste tablic (N,2) punktow (x,y) per
    kontur, odfiltrowanych ponizej MIN_CONTOUR_LEN."""
    if gray.ndim != 2:
        raise ValueError("extract_contours oczekuje obrazu w skali szarosci (2D)")
    gray_u8 = gray.astype(np.uint8) if gray.dtype != np.uint8 else gray
    edges = cv2.Canny(gray_u8, low, high)
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in contours:
        pts = c.reshape(-1, 2).astype(np.float64)
        if len(pts) >= MIN_CONTOUR_LEN:
            out.append(pts)
    return out


def contour_curvatures(points: np.ndarray, step: int = CURVATURE_STEP) -> np.ndarray:
    """Dyskretna krzywizna |dtheta|/ds w kazdym punkcie konturu (traktowany
    jako zamkniety -- tak zwraca je cv2.findContours). krok `step` punktow
    tlumi szum kwantyzacji pikseli. Zwraca tablice dlugosci len(points), albo
    pusta tablice jesli kontur za krotki."""
    n = len(points)
    if n < 2 * step + 1:
        return np.zeros(0, dtype=np.float64)
    idx = np.arange(n)
    prev_idx = (idx - step) % n
    next_idx = (idx + step) % n
    v1 = points[idx] - points[prev_idx]
    v2 = points[next_idx] - points[idx]
    ang1 = np.arctan2(v1[:, 1], v1[:, 0])
    ang2 = np.arctan2(v2[:, 1], v2[:, 0])
    dtheta = ang2 - ang1
    dtheta = (dtheta + np.pi) % (2 * np.pi) - np.pi  # zawin do (-pi, pi]
    len1 = np.linalg.norm(v1, axis=1)
    len2 = np.linalg.norm(v2, axis=1)
    ds = (len1 + len2) / 2.0
    ds = np.where(ds < 1e-9, 1e-9, ds)
    return np.abs(dtheta) / ds


def image_curvatures(gray: np.ndarray, low: int = CANNY_LOW, high: int = CANNY_HIGH,
                      step: int = CURVATURE_STEP) -> np.ndarray:
    """Wszystkie wartosci krzywizny ze wszystkich konturow obrazu, spojone w
    jedna tablice 1D (pusta jesli brak konturow)."""
    contours = extract_contours(gray, low, high)
    pieces = [contour_curvatures(c, step) for c in contours]
    pieces = [p for p in pieces if len(p)]
    if not pieces:
        return np.zeros(0, dtype=np.float64)
    return np.concatenate(pieces)


@dataclass
class CurvatureThreshold:
    kappa_thresh: float
    median: float
    mad: float


def compute_reference_threshold(reference_grays: Sequence[np.ndarray], k: float = K_ROBUST,
                                 low: int = CANNY_LOW, high: int = CANNY_HIGH,
                                 step: int = CURVATURE_STEP) -> CurvatureThreshold:
    """Prog kappa_thresh = mediana + k*MAD (konwencja MAD calego ekosystemu
    TIMDR), wyznaczony WYLACZNIE z obrazow referencyjnych (zdrowych/
    nienaruszonych)."""
    pieces = [image_curvatures(g, low, high, step) for g in reference_grays]
    pieces = [p for p in pieces if len(p)]
    if not pieces:
        raise ValueError("brak punktow konturu w obrazach referencyjnych -- nie mozna wyznaczyc progu")
    pooled = np.concatenate(pieces)
    med = float(np.median(pooled))
    mad = float(np.median(np.abs(pooled - med)))
    thresh = med + k * mad * MAD_TO_STD
    return CurvatureThreshold(kappa_thresh=thresh, median=med, mad=mad)


def region_kappa_values(gray: np.ndarray, roi: Optional[Tuple[int, int, int, int]] = None,
                         low: int = CANNY_LOW, high: int = CANNY_HIGH,
                         step: int = CURVATURE_STEP) -> np.ndarray:
    """Surowe wartosci krzywizny w podanym regionie (roi=(x0,y0,x1,y1) w
    pikselach) lub calym obrazie jesli roi=None. Do testu Mann-Whitney
    miedzy dwoma regionami."""
    sub = gray[roi[1]:roi[3], roi[0]:roi[2]] if roi is not None else gray
    return image_curvatures(sub, low, high, step)


def region_kappa_density(gray: np.ndarray, threshold: CurvatureThreshold,
                          roi: Optional[Tuple[int, int, int, int]] = None,
                          low: int = CANNY_LOW, high: int = CANNY_HIGH,
                          step: int = CURVATURE_STEP) -> float:
    """G_kappa: udzial punktow konturu z kappa > prog referencyjny, w
    podanym regionie. NaN jesli brak punktow konturu w regionie."""
    k = region_kappa_values(gray, roi, low, high, step)
    if len(k) == 0:
        return float("nan")
    return float(np.mean(k > threshold.kappa_thresh))
