"""Minimalne porównanie obrazu do dwóch oznaczonych przykładów.

To nie jest wytrenowany klasyfikator. Wynik jest podobieństwem wizualnym
do dostarczonych obrazów, a nie prawdopodobieństwem usterki.
"""
from __future__ import annotations

import cv2
import numpy as np


def _validate(query: np.ndarray, normal: np.ndarray, anomaly: np.ndarray) -> None:
    images = (query, normal, anomaly)
    if any(image is None or not isinstance(image, np.ndarray) for image in images):
        raise ValueError("Potrzebne są trzy obrazy: badany, prawidłowy i anomalny")
    if any(image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8 for image in images):
        raise ValueError("Obrazy muszą mieć format BGR uint8")
    if query.shape[0] < 64 or query.shape[1] < 64:
        raise ValueError("Obrazy muszą mieć co najmniej 64×64 piksele")
    if normal.shape != query.shape or anomaly.shape != query.shape:
        raise ValueError("Wszystkie trzy obrazy muszą mieć identyczne wymiary")


def _unit(vector: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    return vector / length if length > 1e-12 else np.zeros_like(vector)


def _features(image: np.ndarray) -> np.ndarray:
    small = cv2.resize(image, (128, 128), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    # Kolor, tekstura krawędzi i przybliżona lokalizacja wzoru.
    color = []
    for channel, bins, maximum in ((0, 16, 180), (1, 8, 256)):
        hist = cv2.calcHist([hsv], [channel], None, [bins], [0, maximum]).ravel()
        color.append(hist / max(float(hist.sum()), 1.0))
    color_vector = _unit(np.concatenate(color))

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    gradient = cv2.magnitude(gx, gy)
    texture = np.histogram(np.clip(gradient, 0, 255), bins=16, range=(0, 256))[0].astype(np.float32)
    texture = _unit(texture)

    spatial = cv2.resize(gray, (16, 16), interpolation=cv2.INTER_AREA).astype(np.float32)
    spatial -= spatial.mean()
    spatial = _unit(spatial.ravel())

    # Wagi z góry ustalone; nie są dopasowywane do obrazów użytkownika.
    return np.concatenate((0.3 * color_vector, 0.3 * texture, 0.4 * spatial))


def _similarity(left: np.ndarray, right: np.ndarray) -> float:
    distance = float(np.linalg.norm(left - right))
    return float(np.clip(1.0 - distance / 2.0, 0.0, 1.0))


def compare_anomaly_similarity(
    query: np.ndarray,
    normal: np.ndarray,
    anomaly: np.ndarray,
    *,
    ambiguity_margin: float = 0.05,
) -> dict:
    """Zwraca podobieństwa i nakładkę różnic względem bliższego przykładu.

    ``ambiguity_margin`` jest heurystyką interfejsu, nie skalibrowanym progiem.
    """
    _validate(query, normal, anomaly)
    if not 0 <= ambiguity_margin < 1:
        raise ValueError("ambiguity_margin musi należeć do [0, 1)")

    query_features = _features(query)
    normal_score = _similarity(query_features, _features(normal))
    anomaly_score = _similarity(query_features, _features(anomaly))
    margin = anomaly_score - normal_score
    if abs(margin) < ambiguity_margin:
        verdict = "NIEROZSTRZYGNIĘTE"
    elif margin > 0:
        verdict = "PODOBNE DO ANOMALII"
    else:
        verdict = "PODOBNE DO PRAWIDŁOWEGO"

    nearest = anomaly if margin > 0 else normal
    difference = cv2.absdiff(query, nearest)
    gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
    heatmap = cv2.applyColorMap(gray_difference, cv2.COLORMAP_TURBO)
    overlay = cv2.addWeighted(query, 0.65, heatmap, 0.35, 0)
    return {
        "verdict": verdict,
        "normal_similarity": normal_score,
        "anomaly_similarity": anomaly_score,
        "margin": margin,
        "nearest_reference": "anomaly" if margin > 0 else "normal",
        "difference_overlay": overlay,
        "calibrated_probability": False,
    }
