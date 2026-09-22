"""Porównanie masek ruchu I²D z MOG2 na sekwencjach CDnet 2014.

To benchmark *foreground/change detection*, nie test manipulacji obrazu
ani detektor anomalii UCSD Ped2. Wyniki są liczone osobno per sekwencja.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import cv2
import numpy as np

from fusionengine_v1 import fusion_engine
from i2d_core import Frame, detect_defects, detect_twist

BLOCK_SIZE = 16
METHODS = ("defect", "defect_twist_fusion", "mog2")
FRAME_PATTERN = re.compile(r"in(\d+)\.(?:jpg|jpeg|png)$", re.IGNORECASE)


def _sequence_files(sequence: Path):
    input_dir = sequence / "input"
    gt_dir = sequence / "groundtruth"
    roi_path = sequence / "ROI.bmp"
    time_path = sequence / "temporalROI.txt"
    for required in (input_dir, gt_dir, roi_path, time_path):
        if not required.exists():
            raise ValueError(f"Brak pliku/katalogu CDnet: {required}")
    frames = []
    for path in input_dir.iterdir():
        match = FRAME_PATTERN.fullmatch(path.name)
        if match:
            frames.append((int(match.group(1)), path))
    frames.sort()
    if not frames:
        raise ValueError(f"Brak klatek inNNNNNN w {input_dir}")
    bounds = [int(x) for x in time_path.read_text(encoding="utf-8").split()]
    if len(bounds) != 2 or bounds[0] > bounds[1]:
        raise ValueError(f"Niepoprawny temporalROI.txt: {time_path}")
    roi = cv2.imread(str(roi_path), cv2.IMREAD_GRAYSCALE)
    if roi is None:
        raise ValueError(f"Nie można odczytać ROI: {roi_path}")
    return frames, gt_dir, roi > 0, tuple(bounds)


def _ground_truth(gt_dir: Path, index: int, shape):
    for suffix in ("png", "bmp"):
        path = gt_dir / f"gt{index:06d}.{suffix}"
        if path.exists():
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None or image.shape != shape:
                raise ValueError(f"Błędna maska ground truth: {path}")
            return image
    raise ValueError(f"Brak maski ground truth dla klatki {index} w {gt_dir}")


def _detections_to_mask(detections, shape, block_size=BLOCK_SIZE):
    mask = np.zeros(shape, dtype=bool)
    h, w = shape
    for detection in detections:
        x, y = int(detection.x), int(detection.y)
        if 0 <= x < w and 0 <= y < h:
            mask[y:min(y + block_size, h), x:min(x + block_size, w)] = True
    return mask


def _new_counts():
    return {key: 0 for key in ("tp", "fp", "fn", "tn")}


def _update_counts(counts, predicted, gt, valid):
    positive = gt == 255
    negative = gt == 0
    counts["tp"] += int(np.count_nonzero(predicted & positive & valid))
    counts["fp"] += int(np.count_nonzero(predicted & negative & valid))
    counts["fn"] += int(np.count_nonzero(~predicted & positive & valid))
    counts["tn"] += int(np.count_nonzero(~predicted & negative & valid))


def _metrics(counts, runtime_s, n_frames):
    tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        **counts,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "mean_ms_per_processed_frame": 1000 * runtime_s / n_frames,
    }


def run_sequence(sequence: str | Path, max_frames: int | None = None):
    """Przetwórz jeden film strumieniowo; bez modyfikowania wejścia."""
    sequence = Path(sequence)
    frames, gt_dir, roi, (first, last) = _sequence_files(sequence)
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames musi być dodatnie")
    mog2 = cv2.createBackgroundSubtractorMOG2(
        history=500, varThreshold=16, detectShadows=False
    )
    counts = {name: _new_counts() for name in METHODS}
    runtime = {name: 0.0 for name in METHODS}
    previous_gray = None
    processed = evaluated = 0
    for index, path in frames:
        if max_frames is not None and processed >= max_frames:
            break
        raw = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if raw is None or raw.shape[:2] != roi.shape:
            raise ValueError(f"Błędna klatka lub rozmiar różny od ROI: {path}")
        processed += 1

        start = time.perf_counter()
        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        motion = (np.zeros_like(gray) if previous_gray is None
                  else cv2.absdiff(gray, previous_gray))
        previous_gray = gray
        frame = Frame(index, float(index), raw)
        frame.L, frame.M = gray, motion
        preprocessing_s = time.perf_counter() - start

        start = time.perf_counter()
        defects = detect_defects([frame], block_size=BLOCK_SIZE)
        defect_s = time.perf_counter() - start
        defect_mask = _detections_to_mask(defects, gray.shape)

        start = time.perf_counter()
        twists = detect_twist([frame], block_size=BLOCK_SIZE)
        fused = fusion_engine([frame], defects + twists, block_size=BLOCK_SIZE)
        fusion_extra_s = time.perf_counter() - start
        fusion_mask = _detections_to_mask(fused, gray.shape)

        start = time.perf_counter()
        mog2_mask = mog2.apply(raw) > 0
        mog2_s = time.perf_counter() - start

        runtime["defect"] += preprocessing_s + defect_s
        runtime["defect_twist_fusion"] += preprocessing_s + defect_s + fusion_extra_s
        runtime["mog2"] += mog2_s

        if first <= index <= last:
            gt = _ground_truth(gt_dir, index, roi.shape)
            valid = roi & ((gt == 0) | (gt == 255))
            for name, predicted in (
                ("defect", defect_mask),
                ("defect_twist_fusion", fusion_mask),
                ("mog2", mog2_mask),
            ):
                _update_counts(counts[name], predicted, gt, valid)
            evaluated += 1

    if not evaluated:
        raise ValueError("Nie przetworzono klatek z zakresu temporalROI")
    return {
        "sequence": sequence.name,
        "path": str(sequence.resolve()),
        "processed_frames": processed,
        "evaluated_frames": evaluated,
        "temporal_roi": [first, last],
        "partial_run": max_frames is not None and processed < len(frames),
        "methods": {name: _metrics(counts[name], runtime[name], processed)
                    for name in METHODS},
    }


def run_benchmark(sequences, max_frames=None):
    results = [run_sequence(path, max_frames=max_frames) for path in sequences]
    return {
        "task": "CDnet foreground/change detection (not anomaly or forgery)",
        "status": "PARTIAL" if any(r["partial_run"] for r in results) else "COMPLETE",
        "parameters": {
            "block_size": BLOCK_SIZE,
            "mog2_history": 500,
            "mog2_var_threshold": 16,
            "mog2_detect_shadows": False,
            "valid_gt_labels": [0, 255],
            "ignored_gt_labels": [50, 85, 170],
        },
        "sequences": results,
        "macro_f1": {
            name: float(np.mean([r["methods"][name]["f1"] for r in results]))
            for name in METHODS
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequences", nargs="+", help="Katalogi sekwencji CDnet")
    parser.add_argument("--max-frames", type=int,
                        help="Limit do szybkiego uruchomienia; wynik oznaczony PARTIAL")
    parser.add_argument("--output", help="Ścieżka raportu JSON")
    args = parser.parse_args()
    report = run_benchmark(args.sequences, max_frames=args.max_frames)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
        print(f"Raport: {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
