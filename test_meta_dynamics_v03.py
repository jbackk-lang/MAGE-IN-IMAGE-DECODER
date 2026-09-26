"""test_meta_dynamics_v03.py -- BRAMKA SYNTETYCZNA v0.3 (PREREG_META_DYNAMICS_v0.3.md, sekcja 4) + testy jednostkowe
rho per region. Bramka musi przejsc, ZANIM kod dotknie klipow Test006-Test012."""
import numpy as np
import pytest

from meta_dynamics_v1 import RHO_V3_K, compute_region_reference, region_rho_series
from test_meta_dynamics_v1 import _make_noise_frames, _make_noise_frames_with_patch

FA_GATE = 0.075          # polowa bramki v0.1/v0.2 (0.15) - margines, lekcja z v0.2
NEG_SEEDS = [(10, 20), (98, 99), (1000, 1001), (2000, 2001), (3000, 3001)]
POS_CASES = [((1, 2), (0, 0)), ((3, 4), (2, 3)), ((5, 6), (1, 2))]


def test_reference_accepts_single_clip_and_list():
    a = _make_noise_frames(20, seed=1)
    b = _make_noise_frames(20, seed=2)
    r1 = compute_region_reference(a)
    r2 = compute_region_reference([a, b])
    assert r1.median.shape == r2.median.shape == (16,)
    assert np.all(r2.mad > 0) and r1.k == RHO_V3_K


def test_rho_shapes_and_binary():
    ref = compute_region_reference(_make_noise_frames(30, seed=1))
    rho, exceed = region_rho_series(_make_noise_frames(40, seed=2), ref)
    assert rho.shape == (40,) and exceed.shape == (40, 16) and set(np.unique(rho)) <= {0, 1}


@pytest.mark.parametrize("ref_seed,test_seed", NEG_SEEDS)
def test_gate_negative_pure_noise(ref_seed, test_seed):
    ref = compute_region_reference(_make_noise_frames(30, seed=ref_seed))
    rho, _ = region_rho_series(_make_noise_frames(60, seed=test_seed), ref)
    assert rho.mean() <= FA_GATE, f"falszywe alarmy {rho.mean():.3f} > {FA_GATE}"


@pytest.mark.parametrize("seeds,region", POS_CASES)
def test_gate_positive_injected_local_motion(seeds, region):
    ref = compute_region_reference(_make_noise_frames(30, seed=seeds[0]))
    frames = _make_noise_frames_with_patch(60, seed=seeds[1], patch_window=(40, 50), patch_region=region)
    rho, exceed = region_rho_series(frames, ref)
    win = np.zeros(60, bool)
    win[40:51] = True
    assert rho[win].mean() >= 0.5, f"wykrycie w oknie {rho[win].mean():.2f} < 0.5"
    assert rho[~win].mean() <= FA_GATE, f"alarmy poza oknem {rho[~win].mean():.3f} > {FA_GATE}"
    idx = region[0] * 4 + region[1]
    hits = exceed[win & (rho == 1)]
    assert hits[:, idx].mean() >= 0.8, "flaga powinna wskazywac region wstrzykniecia"
