"""app.py -- dashboard I2D: ekrany + przyklady na zywo dla kazdego z 7
modulow (5 oryginalnych detektorow + META_DYNAMICS v0.1/v0.2 +
CONTOUR_CURVATURE v0.1). Live serwer Flask, wzorowany na konwencji
TIMDR-Industrial-Predict/api.py (ten sam ekosystem, ten sam styl: strona
per modul, gotowy przyklad + mozliwosc wgrania wlasnego pliku).

WAZNE: META_DYNAMICS i CONTOUR_CURVATURE sa jawnie oznaczone jako
eksperymentalne (patrz status_badge nizej) -- ten dashboard NIE ukrywa
ich niepelnego/mieszanego wyniku, tylko go pokazuje wprost przy demo.
"""
from __future__ import annotations

import base64
import io
import os
import tempfile
from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np
from flask import Flask, render_template_string, request, url_for

from i2d_core import (
    Detection,
    Frame,
    detect_defects,
    detect_spectral,
    detect_twist,
    load_image,
    load_video,
    split_layers,
)
from rhythm_analyzer_v1 import detect_rhythm
from colorpsychmap_lambda_psych import detect_color_emotion
from meta_dynamics_v1 import compute_reference_thresholds, compute_video_meta_states
from contour_curvature import compute_reference_threshold, extract_contours, contour_curvatures
from stereo_overlay import make_overlays
from anomaly_similarity import compare_anomaly_similarity

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB, demo/dashboard, nie produkcja
UPLOAD_MAX_FRAMES = 300  # jawny limit RAM dla lokalnego dashboardu
UPLOAD_MAX_TOTAL_PIXELS = 12_000_000  # klatki * rozdzielczość; FFT zajmuje dużo RAM

BASE_DIR = os.path.dirname(__file__)
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
UCSD_TRAIN_DIR = os.path.join(BASE_DIR, "data", "ucsd_ped2", "Train")
UCSD_TEST_DIR = os.path.join(BASE_DIR, "data", "ucsd_ped2", "Test", "Test002")
CASIA_DIR = os.path.join(BASE_DIR, "data", "casia2_splicing_sample")

DETECTION_COLORS = {
    "twist": (255, 255, 0),        # cyan (BGR)
    "defect": (0, 0, 255),         # czerwony
    "spectral_anomaly": (0, 255, 255),
    "spectral_direction": (0, 200, 255),
    "spectral_ring": (0, 165, 255),
    "spectral_peak": (0, 255, 0),
    "rhythm_pulse_L": (255, 0, 255),
    "rhythm_pulse_V": (255, 0, 200),
    "rhythm_pulse_M": (200, 0, 255),
    "rhythm_periodic_L": (255, 128, 0),
    "rhythm_periodic_color": (255, 128, 0),
    "rhythm_periodic_motion": (255, 128, 0),
    "color_hue": (0, 128, 255),
    "color_emotion": (180, 105, 255),
}
DEFAULT_COLOR = (255, 255, 255)


# ---------------------------------------------------------------------------
# Pomoce: kodowanie obrazow, rysowanie nakladek
# ---------------------------------------------------------------------------


def encode_b64(img_bgr: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", img_bgr)
    if not ok:
        raise RuntimeError("nie udalo sie zakodowac obrazu")
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


def draw_detections(frame_bgr: np.ndarray, detections: List[Detection], block_size: int) -> np.ndarray:
    out = frame_bgr.copy()
    for d in detections:
        color = DETECTION_COLORS.get(d.dtype, DEFAULT_COLOR)
        cv2.rectangle(out, (d.x, d.y), (d.x + block_size, d.y + block_size), color, 2)
    return out


def load_upload_frames(file_storage) -> List[Frame]:
    suffix = os.path.splitext(file_storage.filename or "")[1].lower() or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        file_storage.save(tmp.name)
        path = tmp.name
    try:
        if suffix in (".png", ".jpg", ".jpeg", ".bmp"):
            frames = load_image(path)
            if frames[0].raw.shape[0] * frames[0].raw.shape[1] > UPLOAD_MAX_TOTAL_PIXELS:
                raise ValueError("Obraz przekracza limit 12 mln pikseli")
        elif suffix in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
            frames = load_video(path, max_frames=UPLOAD_MAX_FRAMES,
                                max_total_pixels=UPLOAD_MAX_TOTAL_PIXELS)
        else:
            raise ValueError("Obsługiwane formaty: PNG/JPG/BMP oraz MP4/AVI/MOV/MKV/WEBM")
        if not frames:
            raise ValueError("nie znaleziono klatek w przeslanym pliku")
        split_layers(frames)
        return frames
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Rejestr modulow
# ---------------------------------------------------------------------------


def _block_demo_runner(detect_fn: Callable, block_size: int):
    """Fabryka funkcji demo dla modulow opartych na Detection+block_size
    (twist, defect, spectral, rhythm, color) -- dziala identycznie na
    przykladzie kanonicznym i na przeslanym pliku."""

    def run(frames: List[Frame]) -> Tuple[np.ndarray, np.ndarray, str]:
        detections = detect_fn(frames)
        f = frames[len(frames) // 2]  # srodkowa klatka -- najbardziej reprezentatywna
        frame_dets = [d for d in detections if d.frame_id == f.id]
        overlay = draw_detections(f.raw, frame_dets, block_size)
        stats = (f"{len(detections)} detekcji lacznie w {len(frames)} klatce/klatkach "
                 f"({len(frame_dets)} na pokazanej klatce).")
        return f.raw, overlay, stats

    return run


def _meta_dynamics_demo(frames_ref: List[Frame], frames_test: List[Frame]) -> Tuple[np.ndarray, np.ndarray, str]:
    thresholds = compute_reference_thresholds(frames_ref)
    states = compute_video_meta_states(frames_test, thresholds)
    # najbardziej "podejrzana" klatka wg Lambda -- ta, ktora dashboard pokazuje
    idx = int(np.argmax([s.Lambda for s in states]))
    f = frames_test[idx]
    s = states[idx]

    h, w = f.raw.shape[:2]
    rows, cols = 4, 4
    overlay = f.raw.copy()
    for r in range(rows):
        for c in range(cols):
            y0, y1 = r * h // rows, (r + 1) * h // rows
            x0, x1 = c * w // cols, (c + 1) * w // cols
            cv2.rectangle(overlay, (x0, y0), (x1, y1), (80, 80, 80), 1)
    # Historyczne rho jest zachowane w module, ale nie jest zwalidowanym alarmem.
    cv2.putText(overlay, f"Lambda={s.Lambda:.3f} tau={s.tau:.3f} [badawcze]",
                (8, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1, cv2.LINE_AA)

    stats = (f"Klatka {idx+1}/{len(frames_test)} (max Lambda w klipie). "
             f"Lambda={s.Lambda:.4f} (prog={thresholds.lambda_threshold:.4f}), "
             f"tau={s.tau:.4f}, historyczne rho={s.rho} (NIE jest alarmem; bramka v0.2 STOP), "
             f"E={s.E:.2f} (prog={thresholds.energy_threshold:.2f}).")
    return f.raw, overlay, stats


def _contour_curvature_demo(ref_grays: List[np.ndarray], test_bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, str]:
    threshold = compute_reference_threshold(ref_grays)
    gray = cv2.cvtColor(test_bgr, cv2.COLOR_BGR2GRAY)
    overlay = test_bgr.copy()
    n_high = 0
    n_total = 0
    for c in extract_contours(gray):
        k = contour_curvatures(c)
        for (x, y), kappa in zip(c.astype(int), k):
            n_total += 1
            if kappa > threshold.kappa_thresh:
                n_high += 1
                cv2.circle(overlay, (x, y), 2, (0, 0, 255), -1)
            else:
                cv2.circle(overlay, (x, y), 1, (0, 200, 0), -1)
    frac = n_high / n_total if n_total else 0.0
    stats = (f"{n_total} punktow konturu, {n_high} ponad prog krzywizny "
             f"({frac:.1%}) -- prog={threshold.kappa_thresh:.3f} "
             f"(mediana={threshold.median:.3f}, MAD={threshold.mad:.3f}). "
             f"Czerwone = krzywizna > prog (potencjalna granica wklejenia), zielone = ponizej.")
    return test_bgr, overlay, stats


MODULES = {
    "twist": {
        "title": "TwistDetector",
        "layer": "L (jasność)",
        "status": "stable",
        "desc": "Lokalna asymetria jasności bloku pikseli (lewa/prawa, góra/dół) -- 'skręt' sygnałowy tego modułu, NIE związany z krzywizną geometryczną.",
    },
    "defect": {
        "title": "DefectScanner v2",
        "layer": "M (ruch)",
        "status": "stable",
        "desc": "Nagłe zmiany ruchu (zniknięcia, przełączenia) -- próg adaptacyjny mean(M)+2*std(M).",
    },
    "spectral": {
        "title": "SpectralOverlayDetector v2",
        "layer": "F (widmo)",
        "status": "stable",
        "desc": "Anomalie FFT: siatki, linie kierunkowe, pierścienie, piki harmoniczne -- z wykluczeniem składowej DC.",
    },
    "rhythm": {
        "title": "RhythmAnalyzer",
        "layer": "L, C, M",
        "status": "stable",
        "desc": "Pulsowanie/miganie klatka-do-klatki + prawdziwa okresowość (autokorelacja) w L/V/M.",
    },
    "color": {
        "title": "ColorPsychMap Λ-psych",
        "layer": "C (HSV)",
        "status": "stable",
        "desc": "Dominująca emocja koloru w bloku (Hue→emocja) + wykrywanie skoków barwy.",
    },
    "meta_dynamics": {
        "title": "META_DYNAMICS v0.1/v0.2",
        "layer": "M (ruch), siatka 4×4",
        "status": "experimental",
        "status_note": "Λ: częściowy trop (istotne na 1/3 klipów testowych UCSD Ped2). ρ: NOT SUPPORTED (próg MAD nie ma bezpiecznego marginesu -- patrz RESULT_META_DYNAMICS_v0.2.md). Świadomie POZA run_i2d().",
        "desc": "Formalizm Λ-τ-ρ (TIMDR) przeniesiony na pole ruchu wideo -- koncentracja przestrzenna energii ruchu na siatce regionów.",
    },
    "contour_curvature": {
        "title": "CONTOUR_CURVATURE v0.1",
        "layer": "G (kontury 2D)",
        "status": "experimental",
        "status_note": "CZĘŚCIOWO SUPPORTED, niska moc (N=4 obrazy testowe) -- patrz RESULT_CONTOUR_CURVATURE_v0.1.md. Świadomie POZA run_i2d().",
        "desc": "Dyskretna krzywizna konturów (Canny+findContours) -- hipoteza: granice splicingu mają wyższą gęstość szczytów krzywizny niż granice naturalne.",
    },
}


# ---------------------------------------------------------------------------
# Generowanie przykladu kanonicznego (raz przy starcie, cachowane w pamieci)
# ---------------------------------------------------------------------------

_EXAMPLE_CACHE = {}


def get_example(name: str) -> Tuple[str, str, str]:
    if name in _EXAMPLE_CACHE:
        return _EXAMPLE_CACHE[name]

    if name in ("twist", "defect", "spectral", "rhythm", "color"):
        # przyklad kanoniczny: pierwszy dostepny plik CASIA2 (realne zdjecie)
        sample_jpg = sorted(f for f in os.listdir(CASIA_DIR) if f.endswith(".jpg"))[0]
        frames = load_image(os.path.join(CASIA_DIR, sample_jpg))
        split_layers(frames)
        runner = {
            "twist": _block_demo_runner(detect_twist, 16),
            "defect": _block_demo_runner(detect_defects, 16),
            "spectral": _block_demo_runner(detect_spectral, 32),
            "rhythm": _block_demo_runner(detect_rhythm, 16),
            "color": _block_demo_runner(detect_color_emotion, 16),
        }[name]
        before, after, stats = runner(frames)
    elif name == "meta_dynamics":
        train_files = sorted(os.listdir(os.path.join(UCSD_TRAIN_DIR, "Train001")))[:30]
        ref_frames = [Frame(i, float(i), cv2.imread(os.path.join(UCSD_TRAIN_DIR, "Train001", fn)))
                      for i, fn in enumerate(train_files)]
        split_layers(ref_frames)
        test_files = sorted(os.listdir(UCSD_TEST_DIR))
        test_frames = [Frame(i, float(i), cv2.imread(os.path.join(UCSD_TEST_DIR, fn)))
                        for i, fn in enumerate(test_files)]
        split_layers(test_frames)
        before, after, stats = _meta_dynamics_demo(ref_frames, test_frames)
    elif name == "contour_curvature":
        jpgs = sorted(f for f in os.listdir(CASIA_DIR) if f.endswith(".jpg"))
        ref_grays = [cv2.imread(os.path.join(CASIA_DIR, f), cv2.IMREAD_GRAYSCALE) for f in jpgs[:2]]
        test_bgr = cv2.imread(os.path.join(CASIA_DIR, jpgs[-1]))
        before, after, stats = _contour_curvature_demo(ref_grays, test_bgr)
    else:
        raise ValueError(name)

    result = (encode_b64(before), encode_b64(after), stats)
    _EXAMPLE_CACHE[name] = result
    return result


def run_upload(name: str, file_storage) -> Tuple[str, str, str]:
    if name in ("twist", "defect", "spectral", "rhythm", "color"):
        frames = load_upload_frames(file_storage)
        runner = {
            "twist": _block_demo_runner(detect_twist, 16),
            "defect": _block_demo_runner(detect_defects, 16),
            "spectral": _block_demo_runner(detect_spectral, 32),
            "rhythm": _block_demo_runner(detect_rhythm, 16),
            "color": _block_demo_runner(detect_color_emotion, 16),
        }[name]
        before, after, stats = runner(frames)
    elif name == "meta_dynamics":
        frames = load_upload_frames(file_storage)
        if len(frames) < 10:
            raise ValueError("META_DYNAMICS potrzebuje wideo (min. ~10 klatek) -- pojedynczy obraz nie wystarczy do policzenia tau/rho.")
        split_point = max(1, len(frames) // 3)
        ref_frames, test_frames = frames[:split_point], frames[split_point:]
        before, after, stats = _meta_dynamics_demo(ref_frames, test_frames)
        stats += (" (UWAGA: próg referencyjny policzony z pierwszej 1/3 tego samego "
                   "wgranego wideo, nie z osobnego zdrowego zbioru -- tylko demonstracja mechaniki.)")
    elif name == "contour_curvature":
        suffix = os.path.splitext(file_storage.filename or "")[1].lower() or ".png"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            file_storage.save(tmp.name)
            path = tmp.name
        try:
            test_bgr = cv2.imread(path)
            if test_bgr is None:
                raise ValueError("nie udalo sie wczytac obrazu")
            gray = cv2.cvtColor(test_bgr, cv2.COLOR_BGR2GRAY)
            before, after, stats = _contour_curvature_demo([gray], test_bgr)
            stats += " (UWAGA: próg referencyjny policzony z TEGO SAMEGO obrazu -- tylko demonstracja mechaniki.)"
        finally:
            os.unlink(path)
    else:
        raise ValueError(name)
    return encode_b64(before), encode_b64(after), stats


# ---------------------------------------------------------------------------
# Szablony (inline -- dashboard jednoplikowy jak reszta modulow demo repo)
# ---------------------------------------------------------------------------

BASE_STYLE = """
<style>
  body { font-family: -apple-system, Segoe UI, sans-serif; background: #14161a; color: #e6e6e6; margin: 0; padding: 0; }
  header { padding: 24px 32px; border-bottom: 1px solid #2a2d33; }
  header h1 { margin: 0; font-size: 22px; }
  header p { color: #9aa0aa; margin: 6px 0 0; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; padding: 24px 32px; }
  .card { background: #1c1f25; border: 1px solid #2a2d33; border-radius: 10px; padding: 18px; text-decoration: none; color: inherit; display: block; }
  .card:hover { border-color: #4a90e2; }
  .card h3 { margin: 0 0 6px; font-size: 16px; }
  .card p { color: #9aa0aa; font-size: 13px; margin: 6px 0 0; }
  .badge { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-top: 8px; }
  .badge.stable { background: #1e3a2a; color: #6fcf97; }
  .badge.experimental { background: #3a2a1e; color: #f2c94c; }
  .module-page { padding: 24px 32px; max-width: 1100px; }
  .back { color: #4a90e2; text-decoration: none; font-size: 13px; }
  .status-note { background: #2a2118; border-left: 3px solid #f2c94c; padding: 10px 14px; margin: 16px 0; font-size: 13px; color: #f2c94c; }
  .compare { display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }
  .compare figure { margin: 0; flex: 1; min-width: 280px; }
  .compare img { width: 100%; border-radius: 6px; border: 1px solid #2a2d33; }
  .compare figcaption { color: #9aa0aa; font-size: 12px; margin-top: 4px; }
  .stats { background: #1c1f25; padding: 12px 16px; border-radius: 8px; font-size: 13px; color: #cfd3da; border: 1px solid #2a2d33; }
  form.upload { margin: 20px 0; padding: 16px; background: #1c1f25; border: 1px solid #2a2d33; border-radius: 8px; }
  form.upload input[type=submit] { background: #4a90e2; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; }
</style>
"""

INDEX_TEMPLATE = BASE_STYLE + """
<header>
  <h1>I&sup2;D -- dashboard modulow</h1>
  <p>MAGE-IN-IMAGE-DECODER: 7 detektorow, gotowe przyklady + mozliwosc wgrania wlasnego pliku.</p>
</header>
<div class="grid">
  {% for key, m in modules.items() %}
  <a class="card" href="{{ url_for('module_page', name=key) }}">
    <h3>{{ m.title }}</h3>
    <p>{{ m.desc }}</p>
    <p style="color:#6a7180">warstwa: {{ m.layer }}</p>
    <span class="badge {{ m.status }}">{{ 'stabilny' if m.status == 'stable' else 'eksperymentalny' }}</span>
  </a>
  {% endfor %}
  <a class="card" href="{{ url_for('stereo_page') }}">
    <h3>Stereo — szybkie nakładki</h3>
    <p>Dwa obrazy: anaglif i poglądowa mapa przesunięć.</p>
    <span class="badge experimental">podgląd, nie pomiar głębokości</span>
  </a>
  <a class="card" href="{{ url_for('similarity_page') }}">
    <h3>Podobieństwo anomalii — szybki test</h3>
    <p>Porównaj własny obraz z przykładem prawidłowym i anomalnym.</p>
    <span class="badge experimental">heurystyka, nie diagnoza</span>
  </a>
</div>
"""

SIMILARITY_TEMPLATE = BASE_STYLE + """
<header>
  <a class="back" href="{{ url_for('index') }}">&larr; wszystkie moduły</a>
  <h1>Podobieństwo do znanej anomalii</h1>
  <p>Minimalne porównanie trzech obrazów tej samej sceny.</p>
</header>
<div class="module-page">
  <div class="status-note">Wynik mówi tylko, do którego przykładu obraz jest bardziej podobny.
    Liczby nie są prawdopodobieństwem usterki. Użyj tego samego kadru, oświetlenia
    i rozdzielczości; niewielka anomalia może zginąć w tle.</div>
  <form class="upload" method="post" enctype="multipart/form-data">
    <label>Obraz badany: <input type="file" name="query" accept="image/*" required></label><br><br>
    <label>Przykład prawidłowy: <input type="file" name="normal" accept="image/*" required></label><br><br>
    <label>Przykład anomalny: <input type="file" name="anomaly" accept="image/*" required></label><br><br>
    <input type="submit" value="Porównaj podobieństwo">
  </form>
  {% if error %}<div class="status-note">Błąd: {{ error }}</div>{% endif %}
  {% if verdict %}
    <div class="stats"><strong>{{ verdict }}</strong><br>
      Podobieństwo do prawidłowego: {{ normal_score }} &nbsp;|&nbsp;
      do anomalii: {{ anomaly_score }} &nbsp;|&nbsp; różnica: {{ margin }}<br>
      Nakładka różnic względem bliższego przykładu: {{ nearest }}.
    </div>
    <div class="compare">
      <figure><img src="{{ query_image }}"><figcaption>Obraz badany</figcaption></figure>
      <figure><img src="{{ overlay }}"><figcaption>Poglądowa nakładka różnic</figcaption></figure>
    </div>
  {% endif %}
</div>
"""

STEREO_TEMPLATE = BASE_STYLE + """
<header>
  <a class="back" href="{{ url_for('index') }}">&larr; wszystkie moduły</a>
  <h1>Stereo — szybkie nakładki</h1>
  <p>Para obrazów tej samej sceny, najlepiej po rektyfikacji.</p>
</header>
<div class="module-page">
  <div class="status-note">To podgląd anaglifowy i disparycja względna.
    Bez kalibracji kamer nie jest to głębokość w metrach ani detekcja anomalii.</div>
  <form class="upload" method="post" enctype="multipart/form-data">
    <label>Lewy obraz: <input type="file" name="left" accept="image/*" required></label><br><br>
    <label>Prawy obraz: <input type="file" name="right" accept="image/*" required></label><br><br>
    <input type="submit" value="Pokaż nakładki">
  </form>
  {% if error %}<div class="status-note">Błąd: {{ error }}</div>{% endif %}
  {% if anaglyph %}
  <div class="compare">
    <figure><img src="{{ anaglyph }}"><figcaption>Anaglif czerwono-cyjanowy</figcaption></figure>
    <figure><img src="{{ overlay }}"><figcaption>Mapa disparycji na lewym obrazie</figcaption></figure>
    <figure><img src="{{ color }}"><figcaption>Kolorowe przesunięcie (tylko poprawne piksele)</figcaption></figure>
  </div>
  <div class="stats">Udział pikseli z oszacowanym przesunięciem: {{ fraction }}.
    Bez kalibracji brak odległości w metrach.</div>
  {% endif %}
</div>
"""

MODULE_TEMPLATE = BASE_STYLE + """
<header>
  <a class="back" href="{{ url_for('index') }}">&larr; wszystkie moduly</a>
  <h1>{{ m.title }}</h1>
  <p>{{ m.desc }}</p>
  <span class="badge {{ m.status }}">{{ 'stabilny' if m.status == 'stable' else 'eksperymentalny' }}</span>
</header>
<div class="module-page">
  {% if m.status_note %}
  <div class="status-note"><strong>Status wyniku:</strong> {{ m.status_note }}</div>
  {% endif %}

  <h3>Przyklad kanoniczny</h3>
  <div class="compare">
    <figure><img src="{{ before }}"><figcaption>wejście</figcaption></figure>
    <figure><img src="{{ after }}"><figcaption>wynik detekcji (nałożone oznaczenia)</figcaption></figure>
  </div>
  <div class="stats">{{ stats }}</div>

  <h3>Wypróbuj na własnym pliku</h3>
  <form class="upload" method="post" enctype="multipart/form-data" action="{{ url_for('module_page', name=name) }}">
    <input type="file" name="file" required>
    <input type="submit" value="Uruchom detekcję">
  </form>

  {% if upload_before %}
  <h3>Wynik na wgranym pliku</h3>
  <div class="compare">
    <figure><img src="{{ upload_before }}"><figcaption>wejście</figcaption></figure>
    <figure><img src="{{ upload_after }}"><figcaption>wynik detekcji</figcaption></figure>
  </div>
  <div class="stats">{{ upload_stats }}</div>
  {% endif %}
  {% if upload_error %}
  <div class="status-note">Błąd: {{ upload_error }}</div>
  {% endif %}
</div>
"""


@app.route("/")
def index():
    return render_template_string(INDEX_TEMPLATE, modules=MODULES)


@app.route("/stereo", methods=["GET", "POST"])
def stereo_page():
    view = {"anaglyph": None, "overlay": None, "color": None,
            "fraction": None, "error": None}
    if request.method == "POST":
        try:
            images = []
            for key in ("left", "right"):
                upload = request.files.get(key)
                if not upload or not upload.filename:
                    raise ValueError("Wybierz lewy i prawy obraz")
                image = cv2.imdecode(np.frombuffer(upload.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError(f"Nie można odczytać obrazu: {key}")
                if image.shape[0] * image.shape[1] > UPLOAD_MAX_TOTAL_PIXELS:
                    raise ValueError("Obraz przekracza limit 12 mln pikseli")
                images.append(image)
            result = make_overlays(*images)
            view.update(
                anaglyph=encode_b64(result["anaglyph"]),
                overlay=encode_b64(result["disparity_overlay"]),
                color=encode_b64(result["disparity_color"]),
                fraction=f"{result['valid_fraction']:.1%}",
            )
        except (ValueError, cv2.error) as exc:
            view["error"] = str(exc)
    return render_template_string(STEREO_TEMPLATE, **view)


@app.route("/similarity", methods=["GET", "POST"])
def similarity_page():
    view = {"verdict": None, "error": None}
    if request.method == "POST":
        try:
            images = []
            for key in ("query", "normal", "anomaly"):
                upload = request.files.get(key)
                if not upload or not upload.filename:
                    raise ValueError("Wybierz trzy obrazy: badany, prawidłowy i anomalny")
                image = cv2.imdecode(np.frombuffer(upload.read(), dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError(f"Nie można odczytać obrazu: {key}")
                if image.shape[0] * image.shape[1] > UPLOAD_MAX_TOTAL_PIXELS:
                    raise ValueError("Obraz przekracza limit 12 mln pikseli")
                images.append(image)
            result = compare_anomaly_similarity(*images)
            view.update(
                verdict=result["verdict"],
                normal_score=f"{result['normal_similarity']:.3f}",
                anomaly_score=f"{result['anomaly_similarity']:.3f}",
                margin=f"{abs(result['margin']):.3f}",
                nearest="anomalnego" if result["nearest_reference"] == "anomaly" else "prawidłowego",
                query_image=encode_b64(images[0]),
                overlay=encode_b64(result["difference_overlay"]),
            )
        except (ValueError, cv2.error) as exc:
            view["error"] = str(exc)
    return render_template_string(SIMILARITY_TEMPLATE, **view)


@app.route("/demo/<name>", methods=["GET", "POST"])
def module_page(name: str):
    if name not in MODULES:
        return f"nieznany modul: {name}", 404

    before, after, stats = get_example(name)
    upload_before = upload_after = upload_stats = None
    upload_error = None

    if request.method == "POST":
        file_storage = request.files.get("file")
        if file_storage and file_storage.filename:
            try:
                upload_before, upload_after, upload_stats = run_upload(name, file_storage)
            except Exception as exc:  # noqa: BLE001 -- demo dashboard, pokazujemy blad uzytkownikowi
                upload_error = str(exc)

    return render_template_string(
        MODULE_TEMPLATE, m=MODULES[name], name=name,
        before=before, after=after, stats=stats,
        upload_before=upload_before, upload_after=upload_after,
        upload_stats=upload_stats, upload_error=upload_error,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050)
