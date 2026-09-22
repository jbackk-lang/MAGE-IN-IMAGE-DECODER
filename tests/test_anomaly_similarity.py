import io

import cv2
import numpy as np
import pytest

from anomaly_similarity import compare_anomaly_similarity
from app import app


def _samples():
    normal = np.full((96, 128, 3), 30, dtype=np.uint8)
    cv2.rectangle(normal, (30, 20), (80, 75), (170, 170, 170), -1)
    anomaly = np.full((96, 128, 3), 220, dtype=np.uint8)
    cv2.circle(anomaly, (60, 45), 25, (0, 0, 220), -1)
    return normal, anomaly


def _png(image):
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return io.BytesIO(buffer.tobytes())


def test_exact_anomaly_reference_is_closer():
    normal, anomaly = _samples()
    result = compare_anomaly_similarity(anomaly, normal, anomaly)
    assert result["verdict"] == "PODOBNE DO ANOMALII"
    assert result["anomaly_similarity"] == pytest.approx(1.0)
    assert result["normal_similarity"] < result["anomaly_similarity"]
    assert result["difference_overlay"].shape == anomaly.shape
    assert result["calibrated_probability"] is False


def test_same_references_abstain():
    normal, _ = _samples()
    result = compare_anomaly_similarity(normal, normal, normal)
    assert result["verdict"] == "NIEROZSTRZYGNIĘTE"
    assert result["margin"] == pytest.approx(0.0)


def test_mismatched_images_rejected():
    normal, anomaly = _samples()
    with pytest.raises(ValueError, match="identyczne wymiary"):
        compare_anomaly_similarity(anomaly[:80], normal, anomaly)


def test_dashboard_route_shows_result_and_invalid_upload():
    normal, anomaly = _samples()
    client = app.test_client()
    assert client.get("/similarity").status_code == 200
    response = client.post("/similarity", data={
        "query": (_png(anomaly), "query.png"),
        "normal": (_png(normal), "normal.png"),
        "anomaly": (_png(anomaly), "anomaly.png"),
    }, content_type="multipart/form-data")
    assert response.status_code == 200
    assert "PODOBNE DO ANOMALII" in response.get_data(as_text=True)
    assert "data:image/png;base64," in response.get_data(as_text=True)

    bad = client.post("/similarity", data={
        "query": (io.BytesIO(b"bad"), "query.png"),
        "normal": (_png(normal), "normal.png"),
        "anomaly": (_png(anomaly), "anomaly.png"),
    }, content_type="multipart/form-data")
    assert "Nie można odczytać obrazu" in bad.get_data(as_text=True)
