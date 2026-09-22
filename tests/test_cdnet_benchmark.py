"""Mały, lokalny test kontraktu CDnet — bez pobierania i bez strojenia."""
import cv2
import numpy as np
import pytest
import warnings

from cdnet_benchmark import _new_counts, _update_counts, run_benchmark, run_sequence
from download_cdnet import download_sequence
from i2d_core import Frame, detect_twist


def _sequence(tmp_path):
    root = tmp_path / "example"
    (root / "input").mkdir(parents=True)
    (root / "groundtruth").mkdir()
    roi = np.full((32, 32), 255, dtype=np.uint8)
    roi[0, 0] = 0
    cv2.imwrite(str(root / "ROI.bmp"), roi)
    (root / "temporalROI.txt").write_text("2 4\n", encoding="utf-8")
    for number in range(1, 5):
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        ground_truth = np.zeros((32, 32), dtype=np.uint8)
        if number >= 3:
            frame[16:, 16:] = 255
            ground_truth[16:, 16:] = 255
        ground_truth[0, 1] = 170  # nieznany ruch — ignorowany
        cv2.imwrite(str(root / "input" / f"in{number:06d}.jpg"), frame)
        cv2.imwrite(str(root / "groundtruth" / f"gt{number:06d}.png"), ground_truth)
    return root


def test_confusion_ignores_unlabelled_pixels():
    gt = np.array([[255, 0], [170, 85]], dtype=np.uint8)
    pred = np.array([[True, True], [True, True]])
    counts = _new_counts()
    _update_counts(counts, pred, gt, np.isin(gt, [0, 255]))
    assert counts == {"tp": 1, "fp": 1, "fn": 0, "tn": 0}


def test_benchmark_runs_three_methods_and_reports_per_sequence(tmp_path):
    sequence = _sequence(tmp_path)
    result = run_benchmark([sequence])
    assert result["status"] == "COMPLETE"
    assert result["sequences"][0]["evaluated_frames"] == 3
    for method in ("defect", "defect_twist_fusion", "mog2"):
        metrics = result["sequences"][0]["methods"][method]
        assert metrics["tp"] + metrics["fp"] + metrics["fn"] + metrics["tn"] == 3 * (32 * 32 - 2)
        assert 0 <= metrics["f1"] <= 1
        assert metrics["mean_ms_per_processed_frame"] >= 0


def test_partial_run_and_missing_evaluation_are_explicit(tmp_path):
    sequence = _sequence(tmp_path)
    with pytest.raises(ValueError, match="temporalROI"):
        run_sequence(sequence, max_frames=1)
    result = run_benchmark([sequence], max_frames=3)
    assert result["status"] == "PARTIAL"
    assert result["sequences"][0]["evaluated_frames"] == 2


def test_downloader_rejects_unknown_sequence_before_network(tmp_path):
    with pytest.raises(ValueError, match="Dozwolone"):
        download_sequence("unknown", tmp_path)


def test_twist_handles_partial_edge_blocks_without_empty_mean():
    frame = Frame(0, 0.0, np.zeros((33, 33, 3), dtype=np.uint8))
    frame.L = np.zeros((33, 33), dtype=np.uint8)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        assert detect_twist([frame], block_size=16) == []
