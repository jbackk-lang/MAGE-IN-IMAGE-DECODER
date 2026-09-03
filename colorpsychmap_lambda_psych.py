"""
colorpsychmap_lambda_psych.py — ColorPsychMap Λ‑psych
Emocjonalna mapa koloru: Hue -> emocja.

Kanoniczna nazwa pliku (patrz "ColorPsychMap Λ‑psych.py" — cienki
re-eksport zachowany dla wstecznej zgodności, bo nazwa ze spacją i
znakiem Λ nie da się zaimportować standardowym `import`).

Użycie:
    from colorpsychmap_lambda_psych import detect_color_emotion, hue_to_emotion
"""
import numpy as np
from i2d_core import Detection


def hue_to_emotion(hue_deg):
    """
    Prosta mapa Hue -> emocja (Λ-psych)
    hue_deg w stopniach [0, 360)
    """
    if 0 <= hue_deg < 30 or 330 <= hue_deg < 360:
        return "pobudzenie/agresja"
    elif 30 <= hue_deg < 90:
        return "niepokój/napięcie"
    elif 90 <= hue_deg < 150:
        return "akceptacja/spokój"
    elif 150 <= hue_deg < 210:
        return "chłód/dystans"
    elif 210 <= hue_deg < 270:
        return "smutek/nostalgia"
    else:
        return "mistyka/niepewność"


def detect_color_emotion(frames,
                         block_size=16,
                         thr_sat=40.0,
                         thr_val=30.0):
    """
    ColorPsychMap Λ-psych – emocjonalna mapa koloru
    - patrzy na Hue, Saturation, Value
    - wyznacza dominującą emocję w blokach
    """

    detections = []

    for f in frames:
        C = f.C  # HSV
        H = C[:, :, 0].astype(np.float32)
        S = C[:, :, 1].astype(np.float32)
        V = C[:, :, 2].astype(np.float32)

        h, w = H.shape

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                region_H = H[y:y+block_size, x:x+block_size]
                region_S = S[y:y+block_size, x:x+block_size]
                region_V = V[y:y+block_size, x:x+block_size]

                if region_H.size == 0:
                    continue

                mean_H = float(np.mean(region_H)) * 2.0  # OpenCV: 0–180 → 0–360°
                mean_S = float(np.mean(region_S))
                mean_V = float(np.mean(region_V))

                # ignorujemy bardzo słabe, wyprane kolory
                if mean_S < thr_sat or mean_V < thr_val:
                    continue

                emotion = hue_to_emotion(mean_H)

                strength = (mean_S / 255.0) * (mean_V / 255.0)

                detections.append(
                    Detection(
                        f.id,
                        f.time,
                        x,
                        y,
                        "color_emotion",
                        strength,
                        "C",
                        f"emocja: {emotion}"
                    )
                )

    return detections
