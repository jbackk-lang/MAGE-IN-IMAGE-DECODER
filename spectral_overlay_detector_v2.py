"""
spectral_overlay_detector_v2.py — SpectralOverlayDetector v2
Analiza widma (FFT): anomalie, siatki, linie kierunkowe, pierścienie,
piki harmoniczne — z wykluczeniem składowej DC (patrz POPRAWKA niżej).

Kanoniczna nazwa pliku (patrz "SPECTRAL OVERLAY DETECTOR v2.py" — cienki
re-eksport zachowany dla wstecznej zgodności, bo nazwa ze spacją nie da
się zaimportować standardowym `import`).

To jest też JEDYNA prawdziwa implementacja detekcji widmowej w repo —
`i2d_core.py::detect_spectral()` i `i2d_core_defectscanner_v2.py::detect_spectral()`
delegują teraz tutaj zamiast utrzymywać osobne, gorsze kopie tej samej
logiki (patrz komentarze w tamtych plikach).

Użycie:
    from spectral_overlay_detector_v2 import detect_spectral_v2
"""
import numpy as np
from i2d_core import Detection


def detect_spectral_v2(frames,
                       block_size=32,
                       thr_multiplier=3.0,
                       thr_direction=2.5,
                       thr_ring=2.0,
                       dc_radius=3):
    """
    SpectralOverlayDetector v2 – analiza widma (FFT)
    - wykrywa anomalie widmowe, siatki, wzory, modulacje, pierścienie
    - działa na FFT przesuniętym (fftshift)

    POPRAWKA (zweryfikowana empirycznie): składowa DC (częstotliwość zerowa,
    środek widma po fftshift) w naturalnych obrazach ma amplitudę o rzędy
    wielkości większą niż reszta widma. Bez wykluczenia tego regionu
    wszystkie cztery detektory poniżej zgłaszały "anomalię" niemal na KAŻDEJ
    klatce, niezależnie od faktycznej treści obrazu — test na jednolitym,
    szarym obrazie bez żadnej struktury nadal dawał 5/5 pozytywnych detekcji
    (spectral_anomaly, obie linie kierunkowe, ring, peak). `dc_radius`
    (w pikselach) wyklucza kwadrat wokół składowej DC z każdej z czterech
    analiz, żeby wykrywać rzeczywiste anomalie zamiast samej składowej DC.
    """

    detections = []

    for f in frames:
        F = np.abs(f.F)
        h, w = F.shape
        cy, cx = h // 2, w // 2

        y0, y1 = max(0, cy - dc_radius), min(h, cy + dc_radius + 1)
        x0, x1 = max(0, cx - dc_radius), min(w, cx + dc_radius + 1)

        ac_mask = np.ones((h, w), dtype=bool)
        ac_mask[y0:y1, x0:x1] = False
        global_mean = float(np.mean(F[ac_mask])) if np.any(ac_mask) else float(np.mean(F))

        # F z wyzerowaną składową DC — używane w krokach 2 i 4
        F_ac = F.copy()
        F_ac[y0:y1, x0:x1] = 0.0

        # --- 1. ANOMALIE BLOKOWE (pomijamy blok zawierający DC) ---
        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                if y <= cy < y + block_size and x <= cx < x + block_size:
                    continue
                region = F[y:y+block_size, x:x+block_size]
                strength = float(np.mean(region))

                if strength > global_mean * thr_multiplier:
                    detections.append(
                        Detection(
                            f.id, f.time, x, y,
                            "spectral_anomaly",
                            strength,
                            "F",
                            "anomalna energia widma (modulacja / nakładka)"
                        )
                    )

        # --- 2. LINIE KIERUNKOWE (siatki, krzyże, patterny), bez DC ---
        vertical_profile = np.mean(F_ac, axis=0)
        if np.max(vertical_profile) > np.mean(vertical_profile) * thr_direction:
            detections.append(
                Detection(
                    f.id, f.time, 0, 0,
                    "spectral_vertical_line",
                    float(np.max(vertical_profile)),
                    "F",
                    "silna linia pionowa w widmie (siatka / pattern)"
                )
            )

        horizontal_profile = np.mean(F_ac, axis=1)
        if np.max(horizontal_profile) > np.mean(horizontal_profile) * thr_direction:
            detections.append(
                Detection(
                    f.id, f.time, 0, 0,
                    "spectral_horizontal_line",
                    float(np.max(horizontal_profile)),
                    "F",
                    "silna linia pozioma w widmie (siatka / pattern)"
                )
            )

        # --- 3. PIERŚCIENIE WIDMOWE (astronomia, kwarki, rotacja), bez DC ---
        Y, X = np.ogrid[:h, :w]
        R = np.sqrt((X - cx)**2 + (Y - cy)**2)

        radial_bins = np.linspace(dc_radius, np.max(R), 64)
        radial_profile = []

        for i in range(len(radial_bins) - 1):
            mask = (R >= radial_bins[i]) & (R < radial_bins[i+1])
            if np.any(mask):
                radial_profile.append(np.mean(F[mask]))
            else:
                radial_profile.append(0)

        radial_profile = np.array(radial_profile)

        if radial_profile.size and np.max(radial_profile) > np.mean(radial_profile) * thr_ring:
            detections.append(
                Detection(
                    f.id, f.time, cx, cy,
                    "spectral_ring",
                    float(np.max(radial_profile)),
                    "F",
                    "pierścień widmowy (rotacja / rezonans / struktura harmoniczna)"
                )
            )

        # --- 4. PIKI HARMONICZNE (rezonanse, kwarki, modulacje), bez DC ---
        peak = float(np.max(F_ac))

        if peak > global_mean * 4.0:
            detections.append(
                Detection(
                    f.id, f.time, cx, cy,
                    "spectral_peak",
                    peak,
                    "F",
                    "silny pik harmoniczny (rezonans / modulacja)"
                )
            )

    return detections
