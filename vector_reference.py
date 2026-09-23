"""Obrazowe pole wektorowe oceniane względem osobnego zdrowego nagrania.

Inspiracja: referencyjna normalizacja kanałów i RMS z Industrial Predict.
To analogia metody, NIE połączenie z pomiarami łożyska ani diagnoza awarii.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

FEATURE_NAMES = ("median_motion", "p90_motion", "direction_coherence", "mean_abs_curl")
# Minimalna skala techniczna zabezpiecza przed dzieleniem przez zero na
# statycznym nagraniu; nie jest dopasowana do etykiet testowych.
SCALE_FLOOR = np.array([0.05, 0.10, 0.05, 0.01], dtype=np.float64)
GRID_SIZE = (128, 128)


def _features_from_pair(previous: np.ndarray, current: np.ndarray) -> np.ndarray:
    if previous.shape != current.shape or previous.ndim != 3 or previous.shape[2] != 3:
        raise ValueError("Klatki muszą mieć identyczny rozmiar i trzy kanały BGR")
    if previous.dtype != np.uint8 or current.dtype != np.uint8:
        raise ValueError("Klatki muszą mieć typ uint8")
    before = cv2.cvtColor(cv2.resize(previous, GRID_SIZE, interpolation=cv2.INTER_AREA),
                          cv2.COLOR_BGR2GRAY)
    after = cv2.cvtColor(cv2.resize(current, GRID_SIZE, interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(
        before, after, None, pyr_scale=0.5, levels=2, winsize=15,
        iterations=2, poly_n=5, poly_sigma=1.2, flags=0,
    )
    vx, vy = flow[:, :, 0], flow[:, :, 1]
    magnitude = cv2.magnitude(vx, vy)
    mean_magnitude = float(magnitude.mean())
    coherence = (float(np.linalg.norm(flow.mean(axis=(0, 1)))) / mean_magnitude
                 if mean_magnitude > 1e-6 else 0.0)
    curl = np.gradient(vy, axis=1) - np.gradient(vx, axis=0)
    return np.array([
        float(np.median(magnitude)),
        float(np.percentile(magnitude, 90)),
        coherence,
        float(np.mean(np.abs(curl))),
    ], dtype=np.float64)


def extract_video_features(frames: list[np.ndarray]) -> np.ndarray:
    if len(frames) < 2:
        raise ValueError("Potrzebne są przynajmniej dwie klatki")
    if any(frame.shape != frames[0].shape for frame in frames):
        raise ValueError("Klatki filmu muszą mieć identyczny rozmiar")
    return np.vstack([_features_from_pair(a, b) for a, b in zip(frames[:-1], frames[1:])])


def _scores(features: np.ndarray, median: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return np.sqrt(np.mean(((features - median) / scale) ** 2, axis=1))


def fit_healthy_reference(healthy_features: np.ndarray) -> dict:
    """Kalibracja tylko na zdrowym materiale; ostatnie 40% służy kontroli.

    Rozdział jest chronologiczny. Nie używamy klatek badanego filmu do
    skali ani progu. Minimum 20 par ogranicza skrajnie małe referencje.
    """
    features = np.asarray(healthy_features, dtype=np.float64)
    if features.ndim != 2 or features.shape[1] != len(FEATURE_NAMES) or len(features) < 20:
        raise ValueError("Zdrowa referencja wymaga co najmniej 20 par klatek")
    if not np.isfinite(features).all():
        raise ValueError("Cechy referencji muszą być skończone")
    split = max(12, int(len(features) * 0.6))
    train, validation = features[:split], features[split:]
    median = np.median(train, axis=0)
    mad = 1.4826 * np.median(np.abs(train - median), axis=0)
    scale = np.maximum(mad, SCALE_FLOOR)
    validation_scores = _scores(validation, median, scale)
    threshold = max(1.0, float(np.quantile(validation_scores, 0.95)))
    return {
        "feature_names": FEATURE_NAMES,
        "median": median,
        "scale": scale,
        "threshold": threshold,
        "train_pairs": len(train),
        "validation_pairs": len(validation),
        "validation_alert_fraction": float(np.mean(validation_scores > threshold)),
    }


def score_against_reference(test_features: np.ndarray, reference: dict) -> dict:
    features = np.asarray(test_features, dtype=np.float64)
    if features.ndim != 2 or features.shape[1] != len(FEATURE_NAMES) or not len(features):
        raise ValueError("Badany film wymaga co najmniej jednej pary klatek")
    if not np.isfinite(features).all():
        raise ValueError("Cechy badanego filmu muszą być skończone")
    scores = _scores(features, reference["median"], reference["scale"])
    threshold = reference["threshold"]
    alerts = scores > threshold
    # Czasowa trwałość odróżnia pojedynczy skok od całej serii klatek.
    longest_run = 0
    current_run = 0
    for alert in alerts:
        current_run = current_run + 1 if alert else 0
        longest_run = max(longest_run, current_run)
    return {
        "scores": scores.tolist(),
        "threshold": threshold,
        "alert_fraction": float(np.mean(alerts)),
        "longest_alert_run_pairs": longest_run,
        "max_score": float(scores.max()),
        "median_score": float(np.median(scores)),
        "n_pairs": len(scores),
        "calibrated_probability": False,
    }


def read_video(path: str | Path, max_frames: int = 300,
               max_total_pixels: int = 12_000_000,
               min_frames: int = 2) -> tuple[list[np.ndarray], float]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError(f"Nie można otworzyć filmu: {path}")
    frames = []
    total_pixels = 0
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    try:
        while len(frames) < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            total_pixels += frame.shape[0] * frame.shape[1]
            if total_pixels > max_total_pixels:
                raise ValueError("Film przekracza limit 12 mln pikseli łącznie")
            frames.append(frame)
        if len(frames) == max_frames and capture.grab():
            raise ValueError(f"Film przekracza limit {max_frames} klatek; wynik nie będzie po cichu ucięty")
    finally:
        capture.release()
    if len(frames) < min_frames:
        raise ValueError(f"Film wymaga co najmniej {min_frames} klatek")
    if fps <= 0:
        raise ValueError("Film musi podawać poprawne FPS")
    return frames, fps


def analyze_video_pair(healthy_path: str | Path, test_path: str | Path) -> dict:
    healthy, healthy_fps = read_video(healthy_path, min_frames=21)
    test, test_fps = read_video(test_path)
    if healthy[0].shape != test[0].shape:
        raise ValueError("Filmy muszą mieć tę samą rozdzielczość")
    if abs(healthy_fps - test_fps) / healthy_fps > 0.01:
        raise ValueError("Filmy muszą mieć takie samo FPS (tolerancja 1%)")
    reference = fit_healthy_reference(extract_video_features(healthy))
    result = score_against_reference(extract_video_features(test), reference)
    return {
        "method": "healthy_reference_vector_flow_rms",
        "fps": healthy_fps,
        "nominal_frame_interval_s": 1.0 / healthy_fps,
        "pair_times_s": ((np.arange(result["n_pairs"]) + 1) / test_fps).tolist(),
        "time_note": "Czas nominalny z FPS; bez rzeczywistych znaczników VFR nie jest to pełny alignment Chronoprocesu.",
        "features": FEATURE_NAMES,
        "reference_train_pairs": reference["train_pairs"],
        "reference_validation_pairs": reference["validation_pairs"],
        "reference_validation_alert_fraction": reference["validation_alert_fraction"],
        **result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("healthy_video")
    parser.add_argument("test_video")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = analyze_video_pair(args.healthy_video, args.test_video)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(f"Raport: {args.output}")
    else:
        print(payload)


if __name__ == "__main__":
    main()
