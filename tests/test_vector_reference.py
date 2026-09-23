import io

import cv2
import numpy as np
import pytest

from vector_reference import (
    analyze_video_pair,
    extract_video_features,
    fit_healthy_reference,
    score_against_reference,
)
from app import app


def test_reference_is_healthy_only_and_shifted_video_scores_higher():
    rng = np.random.default_rng(7)
    base = rng.integers(0, 256, size=(128, 128, 3), dtype=np.uint8)
    healthy = [base.copy() for _ in range(25)]
    moving = [np.roll(base, 2 * i, axis=1) for i in range(8)]
    reference = fit_healthy_reference(extract_video_features(healthy))
    quiet = score_against_reference(extract_video_features(healthy), reference)
    changed = score_against_reference(extract_video_features(moving), reference)
    assert quiet["alert_fraction"] == 0.0
    assert changed["median_score"] > quiet["median_score"]
    assert changed["alert_fraction"] > 0.0
    assert changed["longest_alert_run_pairs"] >= 1
    assert changed["calibrated_probability"] is False


def test_too_short_or_nonfinite_reference_rejected():
    with pytest.raises(ValueError, match="20 par"):
        fit_healthy_reference(np.zeros((19, 4)))
    invalid = np.zeros((20, 4))
    invalid[0, 0] = np.nan
    with pytest.raises(ValueError, match="skończone"):
        fit_healthy_reference(invalid)


def test_video_feature_shapes_must_match():
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="identyczny rozmiar"):
        extract_video_features([image, cv2.resize(image, (64, 64))])


def test_end_to_end_video_pair_and_dashboard(tmp_path):
    rng = np.random.default_rng(3)
    base = rng.integers(0, 256, size=(128, 128, 3), dtype=np.uint8)

    def save(name, frames):
        path = tmp_path / name
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"),
                                 10.0, (128, 128))
        assert writer.isOpened()
        for frame in frames:
            writer.write(frame)
        writer.release()
        return path

    healthy = save("healthy.avi", [base] * 25)
    test = save("test.avi", [np.roll(base, 2 * index, axis=1) for index in range(8)])
    result = analyze_video_pair(healthy, test)
    assert result["n_pairs"] == 7
    assert len(result["pair_times_s"]) == 7
    assert result["pair_times_s"][-1] == pytest.approx(0.7)
    assert result["alert_fraction"] > 0

    response = app.test_client().post("/vector-reference", data={
        "healthy": (io.BytesIO(healthy.read_bytes()), "healthy.avi"),
        "test": (io.BytesIO(test.read_bytes()), "test.avi"),
    }, content_type="multipart/form-data")
    assert response.status_code == 200
    assert "data:image/png;base64," in response.get_data(as_text=True)
