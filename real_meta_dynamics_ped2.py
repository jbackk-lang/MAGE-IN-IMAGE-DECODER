"""real_meta_dynamics_ped2.py -- runner testu realnego META_DYNAMICS_v0.1 na
podzbiorze UCSD Ped2 (data/ucsd_ped2/), zgodnie z PREREG_META_DYNAMICS_v0.1.md
sekcja 5-6. Uruchamiany DOPIERO po przejsciu obu kontroli syntetycznych w
test_meta_dynamics_v1.py (patrz PREREG sekcja 4, bramka stop-if-failed).

Uzycie: `python3 real_meta_dynamics_ped2.py`
"""
from __future__ import annotations

import glob
import json
import os

import cv2
import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu

from i2d_core import Frame, split_layers
from meta_dynamics_v1 import compute_reference_thresholds, compute_video_meta_states

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, "data", "ucsd_ped2")

TRAIN_CLIPS = ["Train001", "Train002", "Train003", "Train004"]
TEST_CLIPS = ["Test001", "Test002", "Test003"]

N_COMPARISONS = len(TEST_CLIPS) * 2  # Lambda (Mann-Whitney) + rho (Fisher) per klip
ALPHA_CORR = 0.05 / N_COMPARISONS


def _load_clip_frames(split: str, clip: str):
    clip_dir = os.path.join(DATA_DIR, split, clip)
    pngs = sorted(glob.glob(os.path.join(clip_dir, "*.png")))
    if not pngs:
        raise FileNotFoundError(
            f"Brak klatek w {clip_dir} -- uruchom konwersje danych (patrz PREREG sekcja 5)."
        )
    frames = []
    for i, path in enumerate(pngs):
        gray = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        raw = np.stack([gray, gray, gray], axis=-1)
        frames.append(Frame(i, float(i), raw))
    split_layers(frames)
    return frames


def rank_biserial_effect_size(u_stat: float, n1: int, n2: int) -> float:
    """r = 2U/(n1*n2) - 1, r in [-1, 1] -- ta sama definicja co w
    timdr_formalism.pipeline (GIA-TIMDR), reimplementowana lokalnie
    (repo-do-repo, nie import)."""
    return 2.0 * u_stat / (n1 * n2) - 1.0


def effect_size_label(r: float) -> str:
    ar = abs(r)
    if ar < 0.1:
        return "pomijalny"
    if ar < 0.3:
        return "maly"
    if ar < 0.5:
        return "sredni"
    return "duzy"


def run_real_test(verbose: bool = True) -> dict:
    with open(os.path.join(DATA_DIR, "Test", "ground_truth.json")) as f:
        ground_truth = json.load(f)

    ref_frames = []
    for clip in TRAIN_CLIPS:
        ref_frames.extend(_load_clip_frames("Train", clip))
    # UWAGA: re-indeksacja Frame.id po polaczeniu klipow nie jest potrzebna --
    # compute_reference_thresholds() uzywa tylko wartosci Lambda/E, nie id.
    thresholds = compute_reference_thresholds(ref_frames)

    if verbose:
        print(f"Progi referencyjne (z {len(ref_frames)} klatek treningowych, "
              f"{len(TRAIN_CLIPS)} klipow):")
        print(f"  Lambda_threshold = {thresholds.lambda_threshold:.4f}")
        print(f"  E_threshold      = {thresholds.energy_threshold:.4f}")
        print()

    results = {}
    for clip in TEST_CLIPS:
        frames = _load_clip_frames("Test", clip)
        states = compute_video_meta_states(frames, thresholds)

        lam = np.array([s.Lambda for s in states])
        rho = np.array([s.rho for s in states])

        gt_lo, gt_hi = ground_truth[clip]  # 1-indeksowane, inclusive
        n = len(states)
        gt_mask = np.zeros(n, dtype=bool)
        # frame_id w Frame jest 0-indeksowany (kolejnosc wczytania) -- gt_frame
        # z oryginalu jest 1-indeksowane, wiec klatka o indeksie i (0-based)
        # odpowiada 1-based (i+1)
        for i in range(n):
            if gt_lo <= (i + 1) <= gt_hi:
                gt_mask[i] = True

        lam_gt, lam_non_gt = lam[gt_mask], lam[~gt_mask]
        rho_gt, rho_non_gt = rho[gt_mask], rho[~gt_mask]

        # Mann-Whitney U na Lambda (gt vs non-gt)
        if len(lam_gt) >= 1 and len(lam_non_gt) >= 1:
            u_stat, p_mw = mannwhitneyu(lam_gt, lam_non_gt, alternative="two-sided")
            r = rank_biserial_effect_size(u_stat, len(lam_gt), len(lam_non_gt))
        else:
            u_stat, p_mw, r = float("nan"), float("nan"), float("nan")

        # Fisher dokladny na rho (2x2: anomalny/nie x gt/nie)
        a = int(rho_gt.sum())               # gt & anomalny
        b = int(len(rho_gt) - a)             # gt & nie-anomalny
        c = int(rho_non_gt.sum())            # non-gt & anomalny
        d = int(len(rho_non_gt) - c)         # non-gt & nie-anomalny
        odds_ratio, p_fisher = fisher_exact([[a, b], [c, d]])

        significant_mw = p_mw < ALPHA_CORR if np.isfinite(p_mw) else False
        significant_fisher = p_fisher < ALPHA_CORR

        results[clip] = {
            "n_frames": n,
            "n_gt": int(gt_mask.sum()),
            "n_non_gt": int((~gt_mask).sum()),
            "lambda_gt_mean": float(lam_gt.mean()) if len(lam_gt) else None,
            "lambda_non_gt_mean": float(lam_non_gt.mean()) if len(lam_non_gt) else None,
            "mannwhitney_p": float(p_mw),
            "rank_biserial_r": float(r),
            "effect_size_label": effect_size_label(r) if np.isfinite(r) else "n/a",
            "significant_mannwhitney_bonferroni": bool(significant_mw),
            "rho_gt_rate": a / len(rho_gt) if len(rho_gt) else None,
            "rho_non_gt_rate": c / len(rho_non_gt) if len(rho_non_gt) else None,
            "fisher_p": float(p_fisher),
            "fisher_odds_ratio": float(odds_ratio),
            "significant_fisher_bonferroni": bool(significant_fisher),
        }

        if verbose:
            r = results[clip]
            print(f"=== {clip} ({r['n_frames']} klatek, {r['n_gt']} gt / {r['n_non_gt']} non-gt) ===")
            print(f"  Lambda: gt_mean={r['lambda_gt_mean']:.4f} non_gt_mean={r['lambda_non_gt_mean']:.4f}")
            print(f"          Mann-Whitney p={r['mannwhitney_p']:.4g}, r={r['rank_biserial_r']:.3f} "
                  f"({r['effect_size_label']}), istotne (Bonferroni)={r['significant_mannwhitney_bonferroni']}")
            print(f"  rho:    gt_rate={r['rho_gt_rate']:.3f} non_gt_rate={r['rho_non_gt_rate']:.3f}")
            print(f"          Fisher p={r['fisher_p']:.4g}, OR={r['fisher_odds_ratio']:.3f}, "
                  f"istotne (Bonferroni)={r['significant_fisher_bonferroni']}")
            print()

    if verbose:
        print(f"alpha_corr (Bonferroni, {N_COMPARISONS} porownan) = {ALPHA_CORR:.4g}")

    return results


if __name__ == "__main__":
    run_real_test()
