import cv2
import numpy as np

# ============================
#   STRUKTURY DANYCH I²D
# ============================

class Frame:
    def __init__(self, frame_id, time, raw):
        self.id = frame_id
        self.time = time
        self.raw = raw
        self.L = None
        self.C = None
        self.M = None
        self.F = None

class Detection:
    def __init__(self, frame_id, time, x, y, dtype, strength, layer, desc):
        self.frame_id = frame_id
        self.time = time
        self.x = x
        self.y = y
        self.dtype = dtype
        self.strength = strength
        self.layer = layer
        self.desc = desc

# ============================
#   FRAME LOADER
# ============================

def load_video(path):
    cap = cv2.VideoCapture(path)
    frames = []
    frame_id = 0

    while True:
        ret, raw = cap.read()
        if not ret:
            break

        time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        frames.append(Frame(frame_id, time, raw))
        frame_id += 1

    cap.release()
    return frames


def load_image(path):
    """Wczytuje pojedynczy obraz statyczny jako jednoelementową listę Frame.

    (Przeniesione tutaj z i2d_core_defectscanner_v2.py — ten plik jest teraz
    cienkim re-eksportem tego modułu, więc funkcja ma jedno miejsce
    zamieszkania zamiast dwóch niezależnych kopii.)
    """
    raw = cv2.imread(path)
    if raw is None:
        raise FileNotFoundError(f"Nie można wczytać obrazu: {path}")
    return [Frame(0, 0.0, raw)]

# ============================
#   LAYER SPLITTER
# ============================

def split_layers(frames):
    prev_L = None

    for f in frames:
        # Jasność
        f.L = cv2.cvtColor(f.raw, cv2.COLOR_BGR2GRAY)

        # Kolor HSV
        f.C = cv2.cvtColor(f.raw, cv2.COLOR_BGR2HSV)

        # Ruch (różnica klatek)
        if prev_L is None:
            f.M = np.zeros_like(f.L)
        else:
            f.M = cv2.absdiff(f.L, prev_L)

        prev_L = f.L

        # Widmo (FFT)
        F = np.fft.fft2(f.L)
        f.F = np.fft.fftshift(F)

# ============================
#   TWIST DETECTOR (skręt)
# ============================

def detect_twist(frames, block_size=16, threshold=20):
    detections = []

    for f in frames:
        L = f.L
        h, w = L.shape

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                region = L[y:y+block_size, x:x+block_size]
                if region.size == 0:
                    continue

                left = np.mean(region[:, :block_size//2])
                right = np.mean(region[:, block_size//2:])
                top = np.mean(region[:block_size//2, :])
                bottom = np.mean(region[block_size//2:, :])

                T = abs(left - right) + abs(top - bottom)

                if T > threshold:
                    detections.append(
                        Detection(f.id, f.time, x, y, "twist", T, "L",
                                  "lokalna asymetria (skręt)")
                    )

    return detections

# ============================
#   DEFECT SCANNER (ρ)
# ============================

def detect_defects(frames, block_size=16):
    """
    DefectScanner v2 — wykrywa nagłe zmiany ruchu (defekty, zniknięcia,
    przełączenia).

    POPRAWKA: próg był wcześniej stałą liczbą (25), niezależną od
    faktycznego poziomu szumu/ruchu w danym wideo. Teraz używany jest próg
    adaptacyjny mean(M) + 2*std(M) (z dolnym ograniczeniem 10.0) — dokładnie
    ta sama logika, która wcześniej istniała TYLKO w
    i2d_core_defectscanner_v2.py (drugiej, niezależnej kopii tego modułu).
    Ten plik jest teraz jedynym miejscem, gdzie ta logika żyje —
    i2d_core_defectscanner_v2.py deleguje tutaj.
    """
    detections = []

    for f in frames:
        M = f.M
        adaptive_threshold = float(np.mean(M) + 2.0 * np.std(M))
        adaptive_threshold = max(adaptive_threshold, 10.0)  # minimum sensowny próg

        h, w = M.shape

        for y in range(0, h, block_size):
            for x in range(0, w, block_size):
                region = M[y:y+block_size, x:x+block_size]
                if region.size == 0:  # bloki na krawędzi (h/w niepodzielne przez block)
                    continue
                strength = float(np.mean(region))

                if strength > adaptive_threshold:
                    detections.append(
                        Detection(f.id, f.time, x, y, "defect", strength, "M",
                                  "nagła zmiana ruchu (defekt)")
                    )

    return detections

# ============================
#   SPECTRAL OVERLAY DETECTOR
# ============================

def detect_spectral(frames, block_size=32, thr_multiplier=3.0):
    """
    POPRAWKA: ta funkcja była trzecią, niezależną kopią detekcji widmowej
    (obok i2d_core_defectscanner_v2.py i SPECTRAL OVERLAY DETECTOR v2.py) i
    — inaczej niż spectral_overlay_detector_v2.py — nie wykluczała składowej
    DC z widma FFT. Składowa DC ma w naturalnych obrazach amplitudę o rzędy
    wielkości większą niż reszta widma, więc ta funkcja zgłaszała fałszywy
    "spectral_anomaly" na centralnym bloku niemal każdej klatki niezależnie
    od faktycznej treści obrazu.

    Zamiast utrzymywać osobną, gorszą kopię tej samej logiki, deleguje teraz
    do jedynej prawdziwej, przetestowanej implementacji w
    spectral_overlay_detector_v2.py (z wykluczeniem DC). `block_size` i
    `thr_multiplier` zachowane dla wstecznej zgodności sygnatury; reszta
    progów (linie/pierścień/pik) korzysta z domyślnych wartości tamtej
    funkcji.
    """
    from spectral_overlay_detector_v2 import detect_spectral_v2
    return detect_spectral_v2(frames, block_size=block_size, thr_multiplier=thr_multiplier)

# ============================
#   PIPELINE I²D
# ============================

def run_i2d(path, mode="video"):
    """
    Główny pipeline I²D.

    Parametry:
        path  : ścieżka do pliku wideo lub obrazu
        mode  : "video" (domyślnie) lub "image" dla obrazów statycznych PNG/JPG

    Zwraca:
        lista Detection ze WSZYSTKICH pięciu modułów (twist, defect,
        spectral, rhythm, color) — POPRAWKA: wcześniej run_i2d() łączył
        tylko twist+defect+spectral, mimo że README (sekcja 8️⃣ FusionEngine)
        opisuje fuzję jako łączącą "twist, defect, rhythm, color, spectral".
        RhythmAnalyzer i ColorPsychMap Λ-psych nigdy nie trafiały do
        FusionEngine/ReportEngine, chyba że ktoś ręcznie dołożył ich wyniki
        do listy przed wywołaniem fusion_engine(). Importy modułów rhythm/
        color są lokalne (wewnątrz funkcji), żeby uniknąć cyklicznego
        importu — oba te moduły robią `from i2d_core import Detection`.
    """
    if mode == "image":
        frames = load_image(path)
    else:
        frames = load_video(path)

    split_layers(frames)

    from rhythm_analyzer_v1 import detect_rhythm
    from colorpsychmap_lambda_psych import detect_color_emotion

    twist = detect_twist(frames)
    defects = detect_defects(frames)
    spectral = detect_spectral(frames)
    rhythm = detect_rhythm(frames)
    color = detect_color_emotion(frames)

    return twist + defects + spectral + rhythm + color
