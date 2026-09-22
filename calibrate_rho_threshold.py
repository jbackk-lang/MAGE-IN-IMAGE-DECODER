"""calibrate_rho_threshold.py -- sweep k (MAD) na zbiorze kalibracyjnym,
wg PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md. Uzycie:
`python3 calibrate_rho_threshold.py`

WAZNE: siatka kandydacka i regula wyboru sa ZAMROZONE w PREREG -- ten
plik je tylko wykonuje, nie definiuje na nowo.
"""
from __future__ import annotations

import glob
import json
import os

import cv2
import numpy as np

from i2d_core import Frame, split_layers
from meta_dynamics_v1 import compute_reference_thresholds, compute_video_meta_states

_HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_DATA_DIR = os.path.join(_HERE, "data", "ucsd_ped2")
CALIB_DATA_DIR = os.path.join(_HERE, "data", "ucsd_ped2_calibration")

TRAIN_CLIPS = ["Train001", "Train002", "Train003", "Train004"]
CALIB_CLIPS = ["Test004", "Test005"]

K_GRID = [3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.75, 0.5]  # PREREG sekcja 3, malejaco

FALSE_ALARM_GATE = 0.15   # PREREG sekcja 5, warunek 1
MIN_SENSITIVITY = 0.10    # PREREG sekcja 5, warunek 2


def _load_clip_frames(data_dir: str, split: str, clip: str):
    clip_dir = os.path.join(data_dir, split, clip)
    pngs = sorted(glob.glob(os.path.join(clip_dir, "*.png")))
    if not pngs:
        raise FileNotFoundError(f"Brak klatek w {clip_dir}")
    frames = []
    for i, path in enumerate(pngs):
        gray = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        raw = np.stack([gray, gray, gray], axis=-1)
        frames.append(Frame(i, float(i), raw))
    split_layers(frames)
    return frames


def _make_noise_frames(n, size=64, seed=0, mean=128, std=3.0):
    """Ta sama konstrukcja co w test_meta_dynamics_v1.py -- reimplementowana
    tu lokalnie (nie import z pliku testowego) zeby ten skrypt dzialal
    niezaleznie od pytest."""
    rng = np.random.default_rng(seed)
    frames = []
    for i in range(n):
        gray = np.clip(rng.normal(mean, std, size=(size, size)), 0, 255).astype(np.uint8)
        raw = np.stack([gray, gray, gray], axis=-1)
        frames.append(Frame(i, float(i), raw))
    split_layers(frames)
    return frames


def run_calibration(verbose: bool = True) -> dict:
    # referencja (ta sama co main test)
    ref_frames = []
    for clip in TRAIN_CLIPS:
        ref_frames.extend(_load_clip_frames(MAIN_DATA_DIR, "Train", clip))

    # zbior kalibracyjny
    with open(os.path.join(CALIB_DATA_DIR, "Test", "ground_truth.json")) as f:
        calib_gt = json.load(f)

    calib_frames = {clip: _load_clip_frames(CALIB_DATA_DIR, "Test", clip) for clip in CALIB_CLIPS}

    # swieza kontrola negatywna, nowy seed (PREREG sekcja 2)
    neg_ref = _make_noise_frames(30, seed=98)
    neg_test = _make_noise_frames(60, seed=99)

    results = {}
    chosen_k = None

    for k in K_GRID:
        thresholds = compute_reference_thresholds(ref_frames, k=k)

        # false_alarm_rate na swiezej kontroli negatywnej
        neg_thresholds = compute_reference_thresholds(neg_ref, k=k)
        neg_states = compute_video_meta_states(neg_test, neg_thresholds)
        false_alarm_rate = float(np.mean([s.rho for s in neg_states]))

        # calib_sensitivity / calib_non_gt_rate na Test004+Test005 laczenie
        gt_rho, non_gt_rho = [], []
        for clip in CALIB_CLIPS:
            frames = calib_frames[clip]
            states = compute_video_meta_states(frames, thresholds)
            rho = np.array([s.rho for s in states])
            lo, hi = calib_gt[clip]
            n = len(states)
            gt_mask = np.array([lo <= (i + 1) <= hi for i in range(n)])
            gt_rho.extend(rho[gt_mask].tolist())
            non_gt_rho.extend(rho[~gt_mask].tolist())

        calib_sensitivity = float(np.mean(gt_rho)) if gt_rho else float("nan")
        calib_non_gt_rate = float(np.mean(non_gt_rho)) if non_gt_rho else float("nan")

        cond1 = false_alarm_rate < FALSE_ALARM_GATE
        cond2 = calib_sensitivity >= MIN_SENSITIVITY
        cond3 = calib_sensitivity > calib_non_gt_rate
        passes = cond1 and cond2 and cond3

        results[k] = {
            "false_alarm_rate": false_alarm_rate,
            "calib_sensitivity": calib_sensitivity,
            "calib_non_gt_rate": calib_non_gt_rate,
            "cond1_false_alarm_ok": cond1,
            "cond2_sensitivity_ok": cond2,
            "cond3_discriminates": cond3,
            "passes": passes,
        }

        if verbose:
            print(f"k={k}: false_alarm={false_alarm_rate:.3f} (<{FALSE_ALARM_GATE}: {cond1}) "
                  f"sensitivity={calib_sensitivity:.3f} (>={MIN_SENSITIVITY}: {cond2}) "
                  f"non_gt_rate={calib_non_gt_rate:.3f} (sensitivity>non_gt: {cond3}) "
                  f"-> PASSES={passes}")

        if passes and chosen_k is None:
            chosen_k = k  # pierwsze (najwieksze, bo K_GRID malejace) spelniajace wszystko

    if verbose:
        print()
        if chosen_k is not None:
            print(f"WYBRANE k = {chosen_k} (najwieksze z siatki spelniajace wszystkie 3 warunki)")
        else:
            print("KALIBRACJA NEGATYWNA: zadne k z siatki nie spelnia wszystkich warunkow.")

    return {"per_k": results, "chosen_k": chosen_k}


if __name__ == "__main__":
    run_calibration()
