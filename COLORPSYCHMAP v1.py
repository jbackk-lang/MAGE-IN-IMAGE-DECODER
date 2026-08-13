import cv2
import numpy as np
from i2d_core import Detection


def detect_color(frames,
                 block_size=16,
                 thr_hue=15.0,
                 thr_sat=20.0,
                 thr_val=25.0):
    """
    ColorPsychMap v1 – analiza koloru (HSV)
    - wykrywa skoki Hue (odcień), Saturation (nasycenie), Value (jasność)
    - wykrywa pulsowanie koloru i nagłe zmiany barwy
    """

    detections = []

    prev_H = None
    prev_S = None
    prev_V = None

    for f in frames:
        C = f.C  # HSV
        H = C[:, :, 0].astype(np.float32)
        S = C[:, :, 1].astype(np.float32)
        V = C[:, :, 2].astype(np.float32)

        # Różnice między klatkami
        dH = cv2.absdiff(H, prev_H) if prev_H is not None else None
        dS = cv2.absdiff(S, prev_S) if prev_S is not None else None
        dV = cv2.absdiff(V, prev_V) if prev_V is not None else None

        h, w = H.shape

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):

                # --- Odcień (Hue) ---
                if dH is not None:
                    region_dH = dH[y:y+block_size, x:x+block_size]
                    hue_strength = float(np.mean(region_dH))

                    if hue_strength > thr_hue:
                        detections.append(
                            Detection(
                                f.id, f.time, x, y,
                                "color_hue",
                                hue_strength,
                                "C",
                                "nagła zmiana odcienia (Hue) – sygnał emocjonalny"
                            )
                        )

                # --- Nasycenie (Saturation) ---
                if dS is not None:
                    region_dS = dS[y:y+block_size, x:x+block_size]
                    sat_strength = float(np.mean(region_dS))

                    if sat_strength > thr_sat:
                        detections.append(
                            Detection(
                                f.id, f.time, x, y,
                                "color_saturation",
                                sat_strength,
                                "C",
                                "nagła zmiana nasycenia (Saturation)"
                            )
                        )

                # --- Jasność (Value) ---
                if dV is not None:
                    region_dV = dV[y:y+block_size, x:x+block_size]
                    val_strength = float(np.mean(region_dV))

                    if val_strength > thr_val:
                        detections.append(
                            Detection(
                                f.id, f.time, x, y,
                                "color_value",
                                val_strength,
                                "C",
                                "nagła zmiana jasności (Value)"
                            )
                        )

        # aktualizacja poprzednich klatek
        prev_H = H
        prev_S = S
        prev_V = V

    return detections
