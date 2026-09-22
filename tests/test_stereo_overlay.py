import io

import cv2
import numpy as np
import pytest

from stereo_overlay import make_overlays


def _pair():
    rng = np.random.default_rng(17)
    left = rng.integers(0, 256, (96, 160, 3), dtype=np.uint8)
    right = np.zeros_like(left)
    right[:, :-8] = left[:, 8:]
    return left, right


def test_stereo_overlays_have_expected_shape_and_are_nonmetric():
    left, right = _pair()
    result = make_overlays(left, right)
    for key in ("anaglyph", "disparity_overlay", "disparity_color"):
        assert result[key].shape == left.shape
        assert result[key].dtype == np.uint8
    assert 0 <= result["valid_fraction"] <= 1
    assert result["metric_depth"] is False
    left_gray = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
    assert np.array_equal(result["anaglyph"][:, :, 2], left_gray)


def test_stereo_rejects_mismatched_sizes():
    left, right = _pair()
    with pytest.raises(ValueError, match="identycznych wymiarach"):
        make_overlays(left, right[:, :-1])


def test_dashboard_stereo_upload_renders_images():
    from app import app

    left, right = _pair()
    ok_l, encoded_l = cv2.imencode(".png", left)
    ok_r, encoded_r = cv2.imencode(".png", right)
    assert ok_l and ok_r
    client = app.test_client()
    assert client.get("/stereo").status_code == 200
    response = client.post("/stereo", data={
        "left": (io.BytesIO(encoded_l.tobytes()), "left.png"),
        "right": (io.BytesIO(encoded_r.tobytes()), "right.png"),
    }, content_type="multipart/form-data")
    assert response.status_code == 200
    assert b"data:image/png;base64" in response.data
