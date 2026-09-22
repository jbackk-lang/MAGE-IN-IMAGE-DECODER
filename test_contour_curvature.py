"""test_contour_curvatures.py -- kontrole syntetyczne (pozytywna+negatywna)
+ testy jednostkowe dla contour_curvature.py. Patrz
PREREG_CONTOUR_CURVATURE_v0.1.md sekcja 3 dla specyfikacji kontroli -- OBIE
musza przejsc zanim jakikolwiek kod dotknie realnego zbioru forgery/
splicing.

UWAGA metodologiczna (znaleziona empirycznie podczas budowy tego pliku,
patrz komentarz przy MWU nizej): pierwsza wersja tego testu porownywala
Mann-Whitney U na SUROWYCH wartosciach krzywizny punkt-po-punkcie miedzy
dwoma regionami jednego obrazu. To zawyzalo stope falszywych alarmow do
~15-40% (zamiast oczekiwanych ~5%), bo punkty wzdluz TEGO SAMEGO konturu
sa silnie skorelowane (krzywizna zmienia sie plynnie wzdluz krzywej) --
zlamanie zalozenia niezaleznosci obserwacji MWU, ten sam blad, przed
ktorym ostrzega `timdr-signal-framework` (operator okna: partycja na
ROZLACZNE bloki, nie nakladajace sie punkty). Poprawka: jednostka
porownania to JEDEN podsumowujacy sygnal (G_kappa density) PER OBRAZ
(seed), nie punkt konturu -- rozne obrazy sa faktycznie niezalezne.
"""
import numpy as np
import pytest
import cv2
from scipy.stats import mannwhitneyu

from contour_curvature import (
    CurvatureThreshold,
    compute_reference_threshold,
    contour_curvatures,
    extract_contours,
    image_curvatures,
    region_kappa_density,
    region_kappa_values,
)

SIZE = 256


def _natural_image(seed: int, size: int = SIZE, n_blobs: int = 10) -> np.ndarray:
    """Symulacja 'naturalnej' sceny: kilka losowych okragow (gladkie
    granice o niskiej, jednorodnej krzywiznie 1/promien -- jak granice
    obiektow organicznych/cieni), lekko rozmytych dla antyaliasingu."""
    rng = np.random.default_rng(seed)
    img = np.full((size, size), 120, dtype=np.uint8)
    for _ in range(n_blobs):
        cx, cy = rng.integers(20, size - 20, 2)
        r = rng.integers(15, 40)
        val = int(rng.integers(60, 200))
        cv2.circle(img, (int(cx), int(cy)), int(r), val, -1)
    return cv2.GaussianBlur(img, (0, 0), sigmaX=1.0)


def _spliced_image(seed: int, size: int = SIZE,
                    patch_roi: tuple = (160, 160, 220, 220)) -> np.ndarray:
    """Jak _natural_image, ale z wklejonym OSTRYM prostokatem (symulacja
    splicingu -- narozniki 90 stopni o duzo wyzszej krzywiznie niz gladkie
    granice okregow)."""
    img = _natural_image(seed, size).copy()
    x0, y0, x1, y1 = patch_roi
    img[y0:y1, x0:x1] = 240
    return img


# ---------------------------------------------------------------------------
# Testy jednostkowe podstawowych wzorow
# ---------------------------------------------------------------------------


def test_contour_curvatures_straight_line_near_zero():
    # linia prosta -> dtheta=0 wszedzie w WNETRZU (funkcja traktuje kontur
    # jako zamkniety, wiec kilka punktow na obu koncach "zawija sie" na
    # przeciwlegly koniec otwartej linii -- oczekiwane, sprawdzamy wnetrze).
    xs = np.arange(0, 100, 1.0)
    pts = np.stack([xs, np.zeros_like(xs)], axis=1)
    step = 3
    k = contour_curvatures(pts, step=step)
    assert len(k) > 0
    interior = k[step:-step]
    assert np.allclose(interior, 0.0, atol=1e-6)


def test_contour_curvatures_right_angle_corner_spikes():
    # kontur w ksztalcie kwadratu -> krzywizna ma wyrazne maksima w
    # naroznikach (kat ~90st), blisko zera na prostych bokach
    side = np.arange(0, 60, 1.0)
    top = np.stack([side, np.zeros_like(side)], axis=1)
    right = np.stack([np.full_like(side, 59), side], axis=1)
    bottom = np.stack([side[::-1], np.full_like(side, 59)], axis=1)
    left = np.stack([np.zeros_like(side), side[::-1]], axis=1)
    square = np.concatenate([top, right, bottom, left], axis=0)
    k = contour_curvatures(square, step=3)
    assert k.max() > 0.5  # narozniki daja duzy skok kierunku na malym ds
    frac_high = np.mean(k > 0.3)
    assert frac_high < 0.15, f"za duzy udzial punktow o wysokiej krzywiznie ({frac_high:.2%}) jak na kwadrat"


def test_extract_contours_requires_grayscale():
    with pytest.raises(ValueError):
        extract_contours(np.zeros((10, 10, 3), dtype=np.uint8))


def test_extract_contours_finds_something_on_natural_image():
    img = _natural_image(seed=1)
    contours = extract_contours(img)
    assert len(contours) > 0


def test_compute_reference_threshold_requires_nonempty():
    with pytest.raises(ValueError):
        compute_reference_threshold([np.full((32, 32), 128, dtype=np.uint8)])


# ---------------------------------------------------------------------------
# KONTROLA POZYTYWNA (PREREG sekcja 3)
# ---------------------------------------------------------------------------


def test_positive_control_sharp_patch_raises_kappa_density():
    ref_images = [_natural_image(seed=s) for s in range(5, 10)]
    threshold = compute_reference_threshold(ref_images)

    patch_roi = (150, 150, 230, 230)  # margines wokol prostokata 160-220,
    # zeby jego granica (gdzie faktycznie jest krawedz) miescila sie w ROI
    outside_roi = (10, 10, 90, 90)  # daleko od patcha, ten sam rozmiar

    densities_patch, densities_outside = [], []
    for seed in range(100, 160):
        img = _spliced_image(seed, patch_roi=(160, 160, 220, 220))
        d_patch = region_kappa_density(img, threshold, roi=patch_roi)
        d_out = region_kappa_density(img, threshold, roi=outside_roi)
        if not np.isnan(d_patch):
            densities_patch.append(d_patch)
        if not np.isnan(d_out):
            densities_outside.append(d_out)

    assert len(densities_patch) >= 30 and len(densities_outside) >= 30, (
        "za malo prob z wykrywalnymi konturami do wiarygodnego testu"
    )
    dp = np.array(densities_patch)
    do = np.array(densities_outside)
    stat, p = mannwhitneyu(dp, do, alternative="greater")
    assert p < 0.05, (
        f"gestosc szczytow krzywizny w patchu (srednia {dp.mean():.3f}, n={len(dp)}) "
        f"powinna byc istotnie wyzsza niz poza nim (srednia {do.mean():.3f}, n={len(do)}), p={p:.4g}"
    )


# ---------------------------------------------------------------------------
# KONTROLA NEGATYWNA (PREREG sekcja 3)
# ---------------------------------------------------------------------------


def test_negative_control_natural_texture_no_spurious_alarm():
    ref_images = [_natural_image(seed=s) for s in range(200, 205)]
    threshold = compute_reference_threshold(ref_images)

    region_a = (20, 20, 100, 100)
    region_b = (140, 140, 220, 220)

    densities_a, densities_b = [], []
    for seed in range(300, 360):
        img = _natural_image(seed)
        d_a = region_kappa_density(img, threshold, roi=region_a)
        d_b = region_kappa_density(img, threshold, roi=region_b)
        if not np.isnan(d_a):
            densities_a.append(d_a)
        if not np.isnan(d_b):
            densities_b.append(d_b)

    assert len(densities_a) >= 20 and len(densities_b) >= 20, (
        "za malo prob z wykrywalnymi konturami do wiarygodnego testu"
    )
    da = np.array(densities_a)
    db = np.array(densities_b)
    stat, p = mannwhitneyu(da, db, alternative="two-sided")
    assert p >= 0.05, (
        f"dwa naturalne regiony bez wklejenia daly istotna roznice gestosci "
        f"krzywizny (a={da.mean():.3f}, b={db.mean():.3f}, p={p:.4g}) -- "
        f"oczekiwany brak struktury"
    )
