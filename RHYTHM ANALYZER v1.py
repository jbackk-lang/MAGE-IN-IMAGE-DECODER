import cv2
import numpy as np
from i2d_core import Detection


def _autocorr_peak(series, min_lag, max_lag):
    """
    Autokorelacja szeregu czasowego (jasność bloku w kolejnych klatkach)
    dla opóźnień (lagów) z przedziału [min_lag, max_lag].

    Zwraca (najlepszy_lag, znormalizowana_autokorelacja_w_[0,1]).
    Jeśli sygnał jest zbyt krótki albo stały (brak wariancji), zwraca (None, 0.0).
    """
    series = np.asarray(series, dtype=np.float64)
    n = series.shape[0]
    series = series - series.mean()
    denom = float(np.sum(series ** 2))
    if denom <= 1e-9 or n <= max_lag:
        return None, 0.0

    best_lag, best_val = None, 0.0
    for lag in range(max(1, min_lag), min(max_lag, n - 1) + 1):
        num = float(np.sum(series[:n - lag] * series[lag:]))
        val = num / denom
        if val > best_val:
            best_val, best_lag = val, lag
    return best_lag, best_val


def detect_rhythm(frames,
                  block_size=16,
                  thr_pulse_L=20.0,
                  thr_pulse_V=20.0,
                  thr_pulse_M=15.0,
                  min_period=2,
                  max_period=6,
                  thr_periodic=0.5):
    """
    RhythmAnalyzer v1 – wykrywanie pulsowania, migania, sekwencji
    - analizuje jasność (L), jasność HSV (V), ruch (M)
    - wykrywa nagłe zmiany klatka-do-klatki (puls/miganie) w blokach obrazu
    - wykrywa RZECZYWISTĄ okresowość (powtarzalne sekwencje) w przedziale
      [min_period, max_period] klatek, metodą autokorelacji szeregu czasowego
      jasności każdego bloku (POPRAWKA: wcześniej min_period/max_period oraz
      bufory history_L/V/M były zbierane, ale nigdy nieużywane — moduł
      wykrywał tylko pojedyncze skoki klatka-do-klatki, nie okresowość).
    """

    detections = []

    # Bufory poprzednich klatek (do detekcji pulsu klatka-do-klatki)
    prev_L = None
    prev_V = None
    prev_M = None

    # Bufory historii (do analizy okresowości po zakończeniu pętli)
    history_L = []
    history_V = []
    history_M = []

    for f in frames:
        L = f.L
        C = f.C
        M = f.M

        V = C[:, :, 2]  # jasność HSV

        # Różnice między klatkami
        dL = cv2.absdiff(L, prev_L) if prev_L is not None else None
        dV = cv2.absdiff(V, prev_V) if prev_V is not None else None
        dM = cv2.absdiff(M, prev_M) if prev_M is not None else None

        # Zapis do historii (używane niżej do analizy okresowości)
        history_L.append(L)
        history_V.append(V)
        history_M.append(M)

        h, w = L.shape

        # Analiza blokowa — puls klatka-do-klatki
        for y in range(0, h, block_size):
            for x in range(0, w, block_size):

                if dL is not None:
                    region_dL = dL[y:y+block_size, x:x+block_size]
                    pulse_L = float(np.mean(region_dL))
                    if pulse_L > thr_pulse_L:
                        detections.append(
                            Detection(
                                f.id, f.time, x, y,
                                "rhythm_light",
                                pulse_L,
                                "L",
                                "puls jasności (zmiana klatka-do-klatki)"
                            )
                        )

                if dV is not None:
                    region_dV = dV[y:y+block_size, x:x+block_size]
                    pulse_V = float(np.mean(region_dV))
                    if pulse_V > thr_pulse_V:
                        detections.append(
                            Detection(
                                f.id, f.time, x, y,
                                "rhythm_color_light",
                                pulse_V,
                                "C",
                                "puls jasności HSV (zmiana klatka-do-klatki)"
                            )
                        )

                if dM is not None:
                    region_dM = dM[y:y+block_size, x:x+block_size]
                    pulse_M = float(np.mean(region_dM))
                    if pulse_M > thr_pulse_M:
                        detections.append(
                            Detection(
                                f.id, f.time, x, y,
                                "rhythm_motion",
                                pulse_M,
                                "M",
                                "puls ruchu (zmiana klatka-do-klatki)"
                            )
                        )

        prev_L = L
        prev_V = V
        prev_M = M

    # --- Analiza okresowości (rzeczywiste "powtarzalne sekwencje") ---
    n_frames = len(frames)
    if n_frames >= 2 * max_period + 2:
        stack_L = np.stack(history_L).astype(np.float64)
        h, w = stack_L.shape[1], stack_L.shape[2]
        last = frames[-1]

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                block_series = stack_L[:, y:y+block_size, x:x+block_size].mean(axis=(1, 2))
                lag, corr = _autocorr_peak(block_series, min_period, max_period)
                if lag is not None and corr > thr_periodic:
                    detections.append(
                        Detection(
                            last.id, last.time, x, y,
                            "rhythm_periodic",
                            float(corr),
                            "L",
                            f"okresowość ~{lag} klatek (autokorelacja {corr:.2f})"
                        )
                    )

    return detections
