"""Opisowe Λ/τ dla wideo; bez klasyfikatora, progów i automatycznego werdyktu.

To osobny tor badawczy. Nie zmienia zamrożonych testów META_DYNAMICS
v0.1/v0.2 ani nie przywraca odrzuconej flagi rho jako alarmu.
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from i2d_core import load_video, split_layers
from meta_dynamics_v1 import energy_trend, region_energy_series, spatial_concentration


def describe_frames(frames):
    """Zwróć szereg i proste podsumowanie, bez oceny 'anomalny/normalny'."""
    if not frames:
        raise ValueError("Potrzebna jest co najmniej jedna klatka")
    if any(frame.M is None for frame in frames):
        raise ValueError("Najpierw wywołaj split_layers(frames)")
    energies = region_energy_series(frames)
    lam = spatial_concentration(energies)
    total_energy = energies.sum(axis=1)
    tau = energy_trend(total_energy)

    def stats(values):
        return {
            "median": float(np.median(values)),
            "p05": float(np.quantile(values, 0.05)),
            "p95": float(np.quantile(values, 0.95)),
        }

    return {
        "status": "EXPLORATORY_ONLY",
        "interpretation": "Opis ruchu, nie detekcja anomalii ani wynik TIMDR.",
        "n_frames": len(frames),
        "summary": {
            "Lambda": stats(lam),
            "tau": stats(tau),
            "motion_energy": stats(total_energy),
        },
        "series": [
            {
                "frame_id": int(frame.id),
                "time_s": float(frame.time),
                "Lambda": float(lam[i]),
                "tau": float(tau[i]),
                "motion_energy": float(total_energy[i]),
            }
            for i, frame in enumerate(frames)
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", help="Plik wideo do analizy opisowej")
    parser.add_argument("--max-frames", type=int, default=300,
                        help="Maksymalna liczba klatek, domyślnie 300")
    parser.add_argument("--max-total-pixels", type=int, default=12_000_000,
                        help="Limit sumy pikseli klatek, domyślnie 12 mln")
    parser.add_argument("--output", help="Opcjonalna ścieżka raportu JSON")
    args = parser.parse_args()
    frames = load_video(args.video, max_frames=args.max_frames,
                        max_total_pixels=args.max_total_pixels)
    split_layers(frames)
    report = describe_frames(frames)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
