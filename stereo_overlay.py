"""Szybkie nakładki stereoskopowe z pary lewy/prawy obraz.

Wymaga obrazów tej samej wielkości, najlepiej po rektyfikacji. Mapa
disparycji jest poglądowa; bez kalibracji nie daje głębokości w metrach.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def make_overlays(left: np.ndarray, right: np.ndarray) -> dict:
    if left is None or right is None or left.shape != right.shape:
        raise ValueError("Potrzebne są dwa obrazy BGR o identycznych wymiarach")
    if left.ndim != 3 or left.shape[2] != 3 or left.dtype != np.uint8:
        raise ValueError("Obrazy muszą mieć format BGR uint8")
    height, width = left.shape[:2]
    if width < 64 or height < 16:
        raise ValueError("Obrazy stereoskopowe muszą mieć co najmniej 64×16 pikseli")

    left_gray = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
    anaglyph = np.empty_like(left)
    anaglyph[:, :, 2] = left_gray   # czerwony kanał z lewego
    anaglyph[:, :, 1] = right_gray  # zielony + niebieski z prawego
    anaglyph[:, :, 0] = right_gray

    num_disparities = max(16, min(64, (width // 16 - 1) * 16))
    matcher = cv2.StereoSGBM_create(
        minDisparity=0, numDisparities=num_disparities, blockSize=5,
        P1=8 * 25, P2=32 * 25, uniquenessRatio=10,
        speckleWindowSize=50, speckleRange=2, disp12MaxDiff=1,
    )
    disparity = matcher.compute(left_gray, right_gray).astype(np.float32) / 16.0
    valid = np.isfinite(disparity) & (disparity > 0)
    color = np.zeros_like(left)
    overlay = left.copy()
    if np.any(valid):
        low, high = np.percentile(disparity[valid], [5, 95])
        scale = max(float(high - low), 1e-6)
        normalized = np.clip((disparity - low) / scale * 255, 0, 255).astype(np.uint8)
        color = cv2.applyColorMap(normalized, cv2.COLORMAP_TURBO)
        color[~valid] = 0
        blend = cv2.addWeighted(left, 0.45, color, 0.55, 0)
        overlay[valid] = blend[valid]

    return {
        "anaglyph": anaglyph,
        "disparity_overlay": overlay,
        "disparity_color": color,
        "valid_fraction": float(np.mean(valid)),
        "metric_depth": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", help="Lewy obraz")
    parser.add_argument("right", help="Prawy obraz")
    parser.add_argument("--output-dir", default="stereo_output")
    args = parser.parse_args()
    left = cv2.imread(args.left, cv2.IMREAD_COLOR)
    right = cv2.imread(args.right, cv2.IMREAD_COLOR)
    result = make_overlays(left, right)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for key in ("anaglyph", "disparity_overlay", "disparity_color"):
        if not cv2.imwrite(str(output / f"{key}.png"), result[key]):
            raise OSError(f"Nie można zapisać {key}.png")
    (output / "info.json").write_text(json.dumps({
        "valid_fraction": result["valid_fraction"],
        "metric_depth": False,
        "note": "Disparycja poglądowa; brak kalibracji i głębokości w metrach.",
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Nakładki: {output.resolve()}")


if __name__ == "__main__":
    main()
