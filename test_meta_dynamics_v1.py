"""test_meta_dynamics_v1.py -- kontrole syntetyczne (pozytywna+negatywna)
+ testy jednostkowe dla meta_dynamics_v1.py. Patrz PREREG_META_DYNAMICS_v0.1.md
sekcja 4 dla pelnej specyfikacji kontroli -- OBIE musza przejsc zanim
jakikolwiek kod dotknie danych UCSD Ped2 (test_meta_dynamics_ped2_real.py).
"""
import numpy as np
import pytest

from i2d_core import Frame, split_layers
from meta_dynamics_v1 import (
    DEFAULT_GRID,
    compute_reference_thresholds,
    compute_video_meta_states,
    energy_trend,
    region_energy_series,
    spatial_concentration,
)


def _make_noise_frames(n, size=64, seed=0, mean=128, std=3.0):
    rng = np.random.default_rng(seed)
    frames = []
    for i in range(n):
        gray = np.clip(rng.normal(mean, std, size=(size, size)), 0, 255).astype(np.uint8)
        raw = np.stack([gray, gray, gray], axis=-1)
        frames.append(Frame(i, float(i), raw))
    split_layers(frames)
    return frames


def _make_noise_frames_with_patch(n, size=64, seed=0, mean=128, std=3.0,
                                    patch_window=(40, 50), patch_region=(0, 0), grid=DEFAULT_GRID):
    """Jak _make_noise_frames, ale w oknie klatek `patch_window` (wlacznie)
    wstrzykuje jasny, poruszajacy sie patch WYLACZNIE w regionie siatki
    `patch_region` (row, col)."""
    rng = np.random.default_rng(seed)
    rows, cols = grid
    row_edges = np.linspace(0, size, rows + 1).astype(int)
    col_edges = np.linspace(0, size, cols + 1).astype(int)
    r, c = patch_region
    r0, r1 = row_edges[r], row_edges[r + 1]
    c0, c1 = col_edges[c], col_edges[c + 1]

    frames = []
    lo, hi = patch_window
    for i in range(n):
        gray = np.clip(rng.normal(mean, std, size=(size, size)), 0, 255).astype(np.uint8)
        if lo <= i <= hi:
            # patch "porusza sie" (inna losowa podregion pozycja per klatka) --
            # kluczowe dla Frame.M (roznica klatka-do-klatki): staly, nieruchomy
            # jasny blok dawalby zerowa roznice po pierwszej klatce.
            ph = max(1, (r1 - r0) // 3)
            pw = max(1, (c1 - c0) // 3)
            py = r0 + rng.integers(0, max(1, (r1 - r0) - ph))
            px = c0 + rng.integers(0, max(1, (c1 - c0) - pw))
            gray[py:py + ph, px:px + pw] = 250
        raw = np.stack([gray, gray, gray], axis=-1)
        frames.append(Frame(i, float(i), raw))
    split_layers(frames)
    return frames


# ---------------------------------------------------------------------------
# Testy jednostkowe podstawowych wzorow
# ---------------------------------------------------------------------------


def test_spatial_concentration_uniform_energy_gives_zero():
    energies = np.ones((5, 16), dtype=np.float64) * 10.0  # idealnie rownomierne
    lam = spatial_concentration(energies)
    assert np.allclose(lam, 0.0, atol=1e-9)


def test_spatial_concentration_single_region_gives_near_one():
    energies = np.zeros((3, 16), dtype=np.float64)
    energies[:, 0] = 100.0  # cala energia w jednym regionie
    lam = spatial_concentration(energies)
    assert np.all(lam > 0.95)


def test_energy_trend_detects_rising_slope():
    E = np.arange(30, dtype=np.float64)  # idealnie rosnace
    tau = energy_trend(E, w=4)
    assert np.all(tau[5:-5] > 0.9)  # wnetrze (brak efektow brzegowych) ma nachylenie ~1


def test_region_energy_series_requires_split_layers():
    f = Frame(0, 0.0, raw=np.zeros((32, 32, 3), dtype=np.uint8))
    with pytest.raises(ValueError, match="split_layers"):
        region_energy_series([f])


# ---------------------------------------------------------------------------
# KONTROLA POZYTYWNA (PREREG sekcja 4)
# ---------------------------------------------------------------------------


def test_positive_control_injected_local_motion_raises_lambda_and_rho():
    frames_ref = _make_noise_frames(30, seed=1)          # referencja: klatki "zdrowe" (osobny seed)
    frames_test = _make_noise_frames_with_patch(
        60, seed=2, patch_window=(40, 50), patch_region=(0, 0)
    )

    thresholds = compute_reference_thresholds(frames_ref)
    states = compute_video_meta_states(frames_test, thresholds)

    lam = np.array([s.Lambda for s in states])
    rho = np.array([s.rho for s in states])

    window_mask = np.zeros(60, dtype=bool)
    window_mask[40:51] = True

    lam_in = lam[window_mask]
    lam_out = lam[~window_mask]

    assert lam_in.mean() > lam_out.mean(), (
        f"Lambda w oknie wstrzykniecia ({lam_in.mean():.3f}) powinna byc wyzsza "
        f"niz poza nim ({lam_out.mean():.3f})"
    )
    assert rho[window_mask].sum() > 0, "co najmniej czesc klatek w oknie wstrzykniecia powinna byc oflagowana rho=1"


# ---------------------------------------------------------------------------
# KONTROLA NEGATYWNA (PREREG sekcja 4)
# ---------------------------------------------------------------------------


def test_negative_control_pure_noise_gives_no_spurious_alarms():
    frames_ref = _make_noise_frames(30, seed=10)
    frames_test = _make_noise_frames(60, seed=20)  # inny seed, BEZ wstrzykniecia

    thresholds = compute_reference_thresholds(frames_ref)
    states = compute_video_meta_states(frames_test, thresholds)

    rho = np.array([s.rho for s in states])
    false_alarm_rate = rho.mean()
    assert false_alarm_rate < 0.15, (
        f"stopa falszywych alarmow na czystym szumie ({false_alarm_rate:.2%}) "
        f"za wysoka -- MAD-owy prog (k=3.5) powinien dawac rzadkie alarmy na "
        f"danych z tego samego rozkladu co referencja"
    )


# ---------------------------------------------------------------------------
# BRAMKA v0.2 -- powtorzenie obu kontroli z k=2.0 (PREREG_META_DYNAMICS_v0.2.md
# sekcja 2), PO kalibracji w PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md.
# Dopisane OBOK testow k=3.5 wyzej, nie zastepujace ich -- historia obu
# wersji progu zostaje widoczna.
# ---------------------------------------------------------------------------

K_V02 = 2.0


def test_positive_control_k2_injected_local_motion_raises_lambda_and_rho():
    frames_ref = _make_noise_frames(30, seed=1)
    frames_test = _make_noise_frames_with_patch(
        60, seed=2, patch_window=(40, 50), patch_region=(0, 0)
    )

    thresholds = compute_reference_thresholds(frames_ref, k=K_V02)
    states = compute_video_meta_states(frames_test, thresholds)

    lam = np.array([s.Lambda for s in states])
    rho = np.array([s.rho for s in states])
    window_mask = np.zeros(60, dtype=bool)
    window_mask[40:51] = True

    assert lam[window_mask].mean() > lam[~window_mask].mean()
    assert rho[window_mask].sum() > 0


def test_negative_control_k2_borderline_fails_gate_documented_stop():
    """UWAGA: ten test dokumentuje ZNANE, ZDIAGNOZOWANE zatrzymanie
    protokolu (patrz RESULT_META_DYNAMICS_v0.2.md sekcja 2-3), NIE jest
    testem "dziala poprawnie". Na TYM SAMYM scenariuszu syntetycznym co
    oryginalna kontrola negatywna v0.1 (seed=10/20 -- inny niz scenariusz
    uzyty w samej kalibracji, seed=98/99), k=2.0 (wybrane w
    PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md) daje false_alarm_rate
    DOKLADNIE na granicy bramki `<0.15` (formalnie: bramka NIE przechodzi).
    Zgodnie z PREREG_META_DYNAMICS_v0.2.md, to jest STOP -- galaz
    META_DYNAMICS-na-wideo NIE przeszla do ponownego testu na
    Test001-003 z tym k. Jesli ten test kiedys zacznie failowac (np. po
    zmianie w region_energy_series/spatial_concentration), to znaczy, ze
    zachowanie kodu sie zmienilo i RESULT_META_DYNAMICS_v0.2.md trzeba
    zaktualizowac -- nie ze test jest zly."""
    frames_ref = _make_noise_frames(30, seed=10)
    frames_test = _make_noise_frames(60, seed=20)

    thresholds = compute_reference_thresholds(frames_ref, k=K_V02)
    states = compute_video_meta_states(frames_test, thresholds)

    rho = np.array([s.rho for s in states])
    false_alarm_rate = rho.mean()
    assert false_alarm_rate == pytest.approx(0.15, abs=1e-9)
    gate_passes = bool(false_alarm_rate < 0.15)
    assert gate_passes == False, "bramka v0.2 z k=2.0 na tym scenariuszu NIE przechodzi (oczekiwane, patrz RESULT v0.2)"
