"""META_DYNAMICS v0.3 na UCSD Ped2 (PREREG_META_DYNAMICS_v0.3.md): kalibracja k na zbiorze deweloperskim i JEDNORAZOWA
ocena na odlozonych klipach Test006-Test012.

Dane: pelny UCSD Ped2 w ukladzie oryginalu (Train/TrainNNN/*.tif, Test/TestNNN/*.tif, Test/UCSDped2.m), katalog ze
zmiennej PED2_FULL (domyslnie ../data/ucsd_ped2_full obok repo; zrodlo: github.com/junaidwahid/UCSD-Anomaly-dataset,
folder UCSD_Anomaly_Dataset.v1p2/UCSDped2).
Uzycie: python ped2_v03.py calibrate   |   python ped2_v03.py evaluate --output RESULT_META_DYNAMICS_v0.3.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re

import cv2
import numpy as np

from i2d_core import Frame, split_layers
from meta_dynamics_v1 import RHO_V3_K, compute_region_reference, region_rho_series

DATA = os.environ.get("PED2_FULL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "ucsd_ped2_full"))
REF_CLIPS = [f"Train{i:03d}" for i in range(1, 13)]          # referencja zdrowa
NORMAL_CAL = [f"Train{i:03d}" for i in range(13, 17)]        # zdrowe, do kalibracji k
DEV_CLIPS = [f"Test{i:03d}" for i in range(1, 6)]            # deweloperskie (juz ogladane w v0.1/v0.2)
HELDOUT = [f"Test{i:03d}" for i in range(6, 13)]             # odlozone - tylko `evaluate`, jeden raz
K_GRID = [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 8.0]
FA_MAX, MARGIN = 0.02, 0.8                                    # FA <= 0.02 i <= 0.8 * 0.02 (margines)


def load_clip(split: str, clip: str):
    frames = []
    for i, p in enumerate(sorted(glob.glob(os.path.join(DATA, split, clip, "*.tif")))):
        g = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        frames.append(Frame(i, float(i), np.stack([g, g, g], axis=-1)))
    if not frames:
        raise FileNotFoundError(f"brak klatek: {os.path.join(DATA, split, clip)}")
    split_layers(frames)
    return frames


def gt_ranges() -> dict[str, tuple[int, int]]:
    txt = open(os.path.join(DATA, "Test", "UCSDped2.m"), encoding="utf-8", errors="ignore").read()
    rng = re.findall(r"gt_frame\s*=\s*\[(\d+):(\d+)\]", txt)
    return {f"Test{i + 1:03d}": (int(a), int(b)) for i, (a, b) in enumerate(rng)}


def gt_mask(n: int, a: int, b: int) -> np.ndarray:
    m = np.zeros(n, bool)
    m[a - 1:b] = True
    return m


def calibrate() -> dict:
    ref_frames = [load_clip("Train", c) for c in REF_CLIPS]
    normal = [load_clip("Train", c) for c in NORMAL_CAL]
    gt = gt_ranges()
    dev = {c: load_clip("Test", c) for c in DEV_CLIPS}
    rows = []
    for k in K_GRID:
        ref = compute_region_reference(ref_frames, k=k)
        fa_norm = float(np.mean(np.concatenate([region_rho_series(f, ref)[0] for f in normal])))
        ng, g = [], []
        for c, fr in dev.items():
            rho = region_rho_series(fr, ref)[0]
            m = gt_mask(len(rho), *gt[c])
            ng += rho[~m].tolist()
            g += rho[m].tolist()
        rows.append({"k": k, "fa_train013_016": fa_norm, "fa_dev_nongt": float(np.mean(ng)), "det_dev_gt": float(np.mean(g))})
    ok = [r["k"] for r in rows if max(r["fa_train013_016"], r["fa_dev_nongt"]) <= FA_MAX * MARGIN]
    return {"per_k": rows, "chosen_k": min(ok) if ok else None, "frozen_k_in_code": RHO_V3_K}


def fisher_greater(a, b, c, d) -> float:
    """Jednostronny dokladny test Fishera: czy odsetek flag w gt (a/(a+b)) > w non-gt (c/(c+d))."""
    from math import comb
    n1, n2, k = a + b, c + d, a + c
    tot = comb(n1 + n2, k)
    return sum(comb(n1, x) * comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / tot


def evaluate() -> dict:
    ref = compute_region_reference([load_clip("Train", c) for c in REF_CLIPS], k=RHO_V3_K)
    gt = gt_ranges()
    per, G, NG = {}, [], []
    for c in HELDOUT:
        rho = region_rho_series(load_clip("Test", c), ref)[0]
        m = gt_mask(len(rho), *gt[c])
        per[c] = {"n": len(rho), "n_gt": int(m.sum()), "det_gt": float(rho[m].mean()) if m.any() else None,
                  "fa_nongt": float(rho[~m].mean()) if (~m).any() else None}
        G += rho[m].tolist()
        NG += rho[~m].tolist()
    det, fa = float(np.mean(G)), float(np.mean(NG))
    a, b, c_, d = int(sum(G)), len(G) - int(sum(G)), int(sum(NG)), len(NG) - int(sum(NG))
    p = fisher_greater(a, b, c_, d)
    clips_ok = sum(1 for v in per.values() if v["det_gt"] is not None and v["det_gt"] >= max(0.3, 2 * fa))
    crit = {"det_ge_0.5": det >= 0.5, "fa_le_0.10": fa <= 0.10, "fisher_p_lt_0.001": p < 0.001, "clips_ok_ge_5": clips_ok >= 5}
    verdict = "SUPPORTED" if all(crit.values()) else ("NOT SUPPORTED" if not crit["fisher_p_lt_0.001"] else "PARTIALLY SUPPORTED")
    return {"k": RHO_V3_K, "per_clip": per, "pooled": {"det_gt": det, "fa_nongt": fa, "n_gt": len(G), "n_nongt": len(NG),
            "fisher_p": p, "clips_ok": clips_ok}, "criteria": crit, "verdict": verdict}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["calibrate", "evaluate"])
    ap.add_argument("--output")
    a = ap.parse_args()
    res = calibrate() if a.mode == "calibrate" else evaluate()
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    if a.output:
        open(a.output, "w", encoding="utf-8").write(txt + "\n")
    print(txt)
