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

def detect_twist(frames):
    detections = []
    block = 16

    for f in frames:
        L = f.L
        h, w = L.shape

        for y in range(0, h, block):
            for x in range(0, w, block):
                region = L[y:y+block, x:x+block]
                if region.size == 0:
                    continue

                left = np.mean(region[:, :block//2])
                right = np.mean(region[:, block//2:])
                top = np.mean(region[:block//2, :])
                bottom = np.mean(region[block//2:, :])

                T = abs(left - right) + abs(top - bottom)

                if T > 20:  # próg skrętu
                    detections.append(
                        Detection(f.id, f.time, x, y, "twist", T, "L",
                                  "lokalna asymetria (skręt)")
                    )

    return detections

# ============================
#   DEFECT SCANNER (ρ)
# ============================

def detect_defects(frames):
    detections = []
    block = 16

    for f in frames:
        M = f.M
        h, w = M.shape

        for y in range(0, h, block):
            for x in range(0, w, block):
                region = M[y:y+block, x:x+block]
                if region.size == 0:  # POPRAWKA: bloki na krawędzi (h/w niepodzielne przez block)
                    continue
                strength = np.mean(region)

                if strength > 25:  # próg defektu
                    detections.append(
                        Detection(f.id, f.time, x, y, "defect", strength, "M",
                                  "nagła zmiana (defekt)")
                    )

    return detections

# ============================
#   SPECTRAL OVERLAY DETECTOR
# ============================

def detect_spectral(frames):
    detections = []
    block = 32

    for f in frames:
        F = np.abs(f.F)
        h, w = F.shape
        # POPRAWKA WYDAJNOŚCI: np.mean(F) liczone raz na klatkę zamiast raz na
        # każdy blok (dla 640x480 i block=32 to ok. 300x mniej przeliczeń
        # średniej po całej macierzy F na klatkę).
        global_mean = np.mean(F)

        for y in range(0, h, block):
            for x in range(0, w, block):
                region = F[y:y+block, x:x+block]
                strength = np.mean(region)

                if strength > global_mean * 3:  # anomalia widmowa
                    detections.append(
                        Detection(f.id, f.time, x, y, "spectral", strength, "F",
                                  "anomalia widmowa / modulacja")
                    )

    return detections

# ============================
#   PIPELINE I²D
# ============================

def run_i2d(path):
    frames = load_video(path)
    split_layers(frames)

    twist = detect_twist(frames)
    defects = detect_defects(frames)
    spectral = detect_spectral(frames)

    return twist + defects + spectral
