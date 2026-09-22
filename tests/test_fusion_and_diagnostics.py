"""Regresje fuzji, ograniczenia wejścia i opisowego toru TIMDR."""
import numpy as np
import pytest

import i2d_core
from fusionengine_v1 import fusion_engine
from timdr_video_diagnostics import describe_frames


def _frame():
    return i2d_core.Frame(0, 0.0, np.zeros((8, 8, 3), dtype=np.uint8))


def _detection(dtype, strength=10.0, x=0, y=0):
    return i2d_core.Detection(0, 0.0, x, y, dtype, strength, "L", "test")


def test_fusion_requires_two_independent_detector_families():
    frame = _frame()
    assert fusion_engine([frame], [_detection("twist")]) == []
    assert fusion_engine([frame], [
        _detection("spectral_peak"), _detection("spectral_ring")
    ]) == []

    result = fusion_engine([frame], [
        _detection("twist", 5000), _detection("spectral_peak", 0.2)
    ])
    assert len(result) == 1
    assert result[0].dtype == "fusion"
    assert result[0].strength == 2.0  # liczba rodzin, nie suma amplitud


def test_fusion_does_not_join_different_blocks():
    frame = _frame()
    assert fusion_engine([frame], [
        _detection("twist", x=0), _detection("defect", x=16)
    ]) == []


def test_video_loader_rejects_broken_file_and_excess_frames(monkeypatch):
    class ClosedCapture:
        def isOpened(self):
            return False

        def release(self):
            pass

    monkeypatch.setattr(i2d_core.cv2, "VideoCapture", lambda _: ClosedCapture())
    with pytest.raises(ValueError, match="Nie można otworzyć"):
        i2d_core.load_video("missing.mp4")

    class TwoFrameCapture:
        def __init__(self):
            self.n = 0
            self.released = False

        def isOpened(self):
            return True

        def read(self):
            self.n += 1
            return (True, np.zeros((2, 2, 3), dtype=np.uint8)) if self.n <= 2 else (False, None)

        def get(self, _):
            return float(self.n * 100)

        def release(self):
            self.released = True

    cap = TwoFrameCapture()
    monkeypatch.setattr(i2d_core.cv2, "VideoCapture", lambda _: cap)
    with pytest.raises(ValueError, match="limit 1 klatek"):
        i2d_core.load_video("two.mp4", max_frames=1)
    assert cap.released

    cap = TwoFrameCapture()
    with pytest.raises(ValueError, match="limit 4 pikseli"):
        i2d_core.load_video("two.mp4", max_total_pixels=4)
    assert cap.released


def test_timdr_video_diagnostics_has_no_alarm_or_verdict():
    frames = [_frame(), i2d_core.Frame(1, 1.0, np.zeros((8, 8, 3), dtype=np.uint8))]
    frames[0].M = np.zeros((8, 8), dtype=np.uint8)
    frames[1].M = np.zeros((8, 8), dtype=np.uint8)
    frames[1].M[:2, :2] = 255
    report = describe_frames(frames)
    assert report["status"] == "EXPLORATORY_ONLY"
    assert report["n_frames"] == 2
    assert report["series"][1]["Lambda"] > report["series"][0]["Lambda"]
    assert all("rho" not in row and "verdict" not in row for row in report["series"])
    assert np.isfinite(report["summary"]["tau"]["median"])
