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
METHODS = (
    "defect", "defect_motion_pixels", "defect_twist_fusion",
    "fusion_motion_pixels", "vector_flow", "defect_vector_fusion",
    "mog2", "mog2_vector_fusion", "mog2_sparse_lk", "mog2_cached_flow_2",
)
PIXEL_MOTION_THRESHOLD = 10  # dolne ograniczenie progu w detect_defects
VECTOR_MIN_DISPLACEMENT = 1.0  # piksele/klatkę, próg techniczny, nie kalibrowany na GT
VECTOR_MIN_COHERENCE = 0.75    # zgodność kierunku wektorów w bloku
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


def _coherent_flow_mask(flow, block_size=BLOCK_SIZE,
                        min_displacement=VECTOR_MIN_DISPLACEMENT,
                        min_coherence=VECTOR_MIN_COHERENCE):
    """Maska bloków o wystarczającym i spójnym kierunkowo przepływie.

    Decyzja dotyczy całego bloku wektorów, nie jasności pojedynczego piksela.
    """
    if flow.ndim != 3 or flow.shape[2] != 2:
        raise ValueError("flow musi mieć dwa kanały vx/vy")
    if block_size < 1:
        raise ValueError("block_size musi być dodatni")
    height, width = flow.shape[:2]
    blocks_y = (height + block_size - 1) // block_size
    blocks_x = (width + block_size - 1) // block_size
    pad_y = blocks_y * block_size - height
    pad_x = blocks_x * block_size - width
    vectors = np.pad(flow, ((0, pad_y), (0, pad_x), (0, 0)))
    magnitudes = np.pad(np.linalg.norm(flow, axis=2), ((0, pad_y), (0, pad_x)))
    vectors = vectors.reshape(blocks_y, block_size, blocks_x, block_size, 2)
    magnitudes = magnitudes.reshape(blocks_y, block_size, blocks_x, block_size)
    y_counts = np.minimum(block_size, height - np.arange(blocks_y) * block_size)
    x_counts = np.minimum(block_size, width - np.arange(blocks_x) * block_size)
    counts = y_counts[:, None] * x_counts[None, :]
    mean_vectors = vectors.sum(axis=(1, 3)) / counts[:, :, None]
    mean_magnitudes = magnitudes.sum(axis=(1, 3)) / counts
    displacement = np.linalg.norm(mean_vectors, axis=2)
    coherence = np.divide(displacement, mean_magnitudes,
                          out=np.zeros_like(displacement), where=mean_magnitudes > 1e-6)
    selected = (displacement >= min_displacement) & (coherence >= min_coherence)
    return np.repeat(np.repeat(selected, block_size, axis=0), block_size, axis=1)[:height, :width]


def _dense_vector_mask(previous_gray, gray, elapsed_frames=1):
    """Piramidalny dense flow na połowie rozdzielczości, przeliczony na px/klatkę."""
    small_size = (max(32, gray.shape[1] // 2), max(32, gray.shape[0] // 2))
    flow = cv2.calcOpticalFlowFarneback(
        cv2.resize(previous_gray, small_size, interpolation=cv2.INTER_AREA),
        cv2.resize(gray, small_size, interpolation=cv2.INTER_AREA), None,
        pyr_scale=0.5, levels=2, winsize=15, iterations=2,
        poly_n=5, poly_sigma=1.2, flags=0,
    )
    flow = cv2.resize(flow, (gray.shape[1], gray.shape[0]),
                      interpolation=cv2.INTER_LINEAR)
    flow[:, :, 0] *= gray.shape[1] / small_size[0] / elapsed_frames
    flow[:, :, 1] *= gray.shape[0] / small_size[1] / elapsed_frames
    return _coherent_flow_mask(flow)


def _sparse_candidate_mask(previous_gray, gray, candidate_mask,
                           block_size=BLOCK_SIZE):
    """LK śledzi cechy tylko w ROI MOG2, następnie agreguje wektory blokowo.

    Dense Farnebäck nie potrafi sensownie działać na dowolnym zbiorze
    pojedynczych pikseli: potrzebuje sąsiedztwa. Tu ROI służy do wyboru
    punktów Shi-Tomasi, a piramidalny LK śledzi jedynie te punkty.
    """
    height, width = gray.shape
    empty = np.zeros((height, width), dtype=bool)
    if previous_gray is None or not np.any(candidate_mask):
        return empty
    small_size = (max(32, width // 2), max(32, height // 2))
    previous_small = cv2.resize(previous_gray, small_size, interpolation=cv2.INTER_AREA)
    gray_small = cv2.resize(gray, small_size, interpolation=cv2.INTER_AREA)
    roi_small = cv2.resize(candidate_mask.astype(np.uint8), small_size,
                           interpolation=cv2.INTER_NEAREST)
    roi_small = cv2.dilate(roi_small, np.ones((5, 5), dtype=np.uint8))
    points = cv2.goodFeaturesToTrack(previous_small, maxCorners=1200,
                                     qualityLevel=0.01, minDistance=3,
                                     mask=roi_small, blockSize=3)
    if points is None:
        return empty
    tracked, status, _ = cv2.calcOpticalFlowPyrLK(
        previous_small, gray_small, points, None,
        winSize=(15, 15), maxLevel=2,
        criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
    )
    if tracked is None or status is None:
        return empty
    previous_points = points.reshape(-1, 2)
    tracked_points = tracked.reshape(-1, 2)
    good = status.reshape(-1).astype(bool)
    good &= np.isfinite(tracked_points).all(axis=1)
    good &= (tracked_points[:, 0] >= 0) & (tracked_points[:, 0] < small_size[0])
    good &= (tracked_points[:, 1] >= 0) & (tracked_points[:, 1] < small_size[1])
    if not np.any(good):
        return empty
    sx, sy = width / small_size[0], height / small_size[1]
    end = tracked_points[good]
    displacement = (end - previous_points[good]) * np.array([sx, sy], dtype=np.float32)
    bx = np.clip((end[:, 0] * sx // block_size).astype(int), 0, (width - 1) // block_size)
    by = np.clip((end[:, 1] * sy // block_size).astype(int), 0, (height - 1) // block_size)
    blocks_x = (width + block_size - 1) // block_size
    blocks_y = (height + block_size - 1) // block_size
    flat_index = by * blocks_x + bx
    n_blocks = blocks_x * blocks_y
    counts = np.bincount(flat_index, minlength=n_blocks)
    sum_x = np.bincount(flat_index, weights=displacement[:, 0], minlength=n_blocks)
    sum_y = np.bincount(flat_index, weights=displacement[:, 1], minlength=n_blocks)
    lengths = np.linalg.norm(displacement, axis=1)
    sum_lengths = np.bincount(flat_index, weights=lengths, minlength=n_blocks)
    net = np.hypot(sum_x, sum_y)
    mean_displacement = np.divide(net, counts, out=np.zeros_like(net), where=counts > 0)
    coherence = np.divide(net, sum_lengths, out=np.zeros_like(net), where=sum_lengths > 1e-6)
    selected = ((counts >= 2) & (mean_displacement >= VECTOR_MIN_DISPLACEMENT) &
                (coherence >= VECTOR_MIN_COHERENCE)).reshape(blocks_y, blocks_x)
    return np.repeat(np.repeat(selected, block_size, axis=0), block_size, axis=1)[:height, :width]


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
    cached_gray = None
    cached_vector_mask = None
    cached_at_frame = None
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
        frame = Frame(index, float(index), raw)
        frame.L, frame.M = gray, motion
        preprocessing_s = time.perf_counter() - start

        start = time.perf_counter()
        defects = detect_defects([frame], block_size=BLOCK_SIZE)
        defect_s = time.perf_counter() - start
        defect_mask = _detections_to_mask(defects, gray.shape)

        start = time.perf_counter()
        motion_pixels = motion > PIXEL_MOTION_THRESHOLD
        defect_pixel_mask = defect_mask & motion_pixels
        pixel_refine_s = time.perf_counter() - start

        start = time.perf_counter()
        twists = detect_twist([frame], block_size=BLOCK_SIZE)
        fused = fusion_engine([frame], defects + twists, block_size=BLOCK_SIZE)
        fusion_extra_s = time.perf_counter() - start
        fusion_mask = _detections_to_mask(fused, gray.shape)

        start = time.perf_counter()
        fusion_pixel_mask = fusion_mask & motion_pixels
        fusion_refine_s = time.perf_counter() - start

        start = time.perf_counter()
        if previous_gray is None:
            vector_mask = np.zeros_like(defect_mask)
        else:
            vector_mask = _dense_vector_mask(previous_gray, gray)
        vector_s = time.perf_counter() - start
        start = time.perf_counter()
        defect_vector_mask = defect_mask & vector_mask
        vector_fusion_s = time.perf_counter() - start
        start = time.perf_counter()
        mog2_mask = mog2.apply(raw) > 0
        mog2_s = time.perf_counter() - start
        start = time.perf_counter()
        mog2_vector_mask = mog2_mask & vector_mask
        mog2_vector_fusion_s = time.perf_counter() - start

        start = time.perf_counter()
        sparse_vector_mask = _sparse_candidate_mask(previous_gray, gray, mog2_mask)
        sparse_s = time.perf_counter() - start
        start = time.perf_counter()
        mog2_sparse_mask = mog2_mask & sparse_vector_mask
        sparse_fusion_s = time.perf_counter() - start

        start = time.perf_counter()
        if previous_gray is None:
            cached_vector_mask = np.zeros_like(mog2_mask)
        elif processed % 2 == 0:
            basis = cached_gray if cached_gray is not None else previous_gray
            elapsed = processed - cached_at_frame if cached_at_frame is not None else 1
            cached_vector_mask = _dense_vector_mask(basis, gray, elapsed_frames=elapsed)
            cached_gray = gray
            cached_at_frame = processed
        cached_flow_s = time.perf_counter() - start
        start = time.perf_counter()
        mog2_cached_mask = mog2_mask & cached_vector_mask
        cached_fusion_s = time.perf_counter() - start
        previous_gray = gray

        runtime["defect"] += preprocessing_s + defect_s
        runtime["defect_motion_pixels"] += preprocessing_s + defect_s + pixel_refine_s
        runtime["defect_twist_fusion"] += preprocessing_s + defect_s + fusion_extra_s
        runtime["fusion_motion_pixels"] += (preprocessing_s + defect_s +
                                             fusion_extra_s + pixel_refine_s + fusion_refine_s)
        runtime["vector_flow"] += preprocessing_s + vector_s
        runtime["defect_vector_fusion"] += (preprocessing_s + defect_s +
                                            vector_s + vector_fusion_s)
        runtime["mog2"] += mog2_s
        runtime["mog2_vector_fusion"] += (preprocessing_s + vector_s +
                                           mog2_s + mog2_vector_fusion_s)
        runtime["mog2_sparse_lk"] += (preprocessing_s + mog2_s +
                                       sparse_s + sparse_fusion_s)
        runtime["mog2_cached_flow_2"] += (preprocessing_s + mog2_s +
                                           cached_flow_s + cached_fusion_s)

        if first <= index <= last:
            gt = _ground_truth(gt_dir, index, roi.shape)
            valid = roi & ((gt == 0) | (gt == 255))
            for name, predicted in (
                ("defect", defect_mask),
                ("defect_motion_pixels", defect_pixel_mask),
                ("defect_twist_fusion", fusion_mask),
                ("fusion_motion_pixels", fusion_pixel_mask),
                ("vector_flow", vector_mask),
                ("defect_vector_fusion", defect_vector_mask),
                ("mog2", mog2_mask),
                ("mog2_vector_fusion", mog2_vector_mask),
                ("mog2_sparse_lk", mog2_sparse_mask),
                ("mog2_cached_flow_2", mog2_cached_mask),
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
            "pixel_motion_threshold": PIXEL_MOTION_THRESHOLD,
            "vector_min_displacement_px_per_frame": VECTOR_MIN_DISPLACEMENT,
            "vector_min_directional_coherence": VECTOR_MIN_COHERENCE,
            "sparse_lk_max_corners": 1200,
            "sparse_lk_min_tracks_per_block": 2,
            "cached_flow_interval_frames": 2,
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
