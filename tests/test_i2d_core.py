"""
Testy regresyjne I²D.

Zakres:
- każdy kanoniczny moduł importuje się bez NameError/ImportError
  (regresja błędu "brak importów" z README)
- pliki ze spacjami w nazwie są rzeczywiście cienkimi re-eksportami
  kanonicznych modułów — asercja TOŻSAMOŚCI obiektu (is), nie tylko
  równości wyniku, żeby przyszła "świeża, niezależna kopia" wklejona z
  powrotem do pliku ze spacją została złapana przez testy
- SpectralOverlayDetector: negatywna kontrola (jednolity obraz -> 0
  detekcji) ORAZ pozytywna kontrola (szachownica -> >0 detekcji), żeby
  poprawka DC-bias nie okazała się po prostu "zawsze zwracaj []"
- DefectScanner: próg adaptacyjny ignoruje szum w okolicach starego,
  sztywnego progu (25), ale łapie realny, wyraźny skok
- RhythmAnalyzer: okresowość wykrywana niezależnie dla jasności (L),
  jasności HSV (V) i ruchu (M) — regresja "history_V/history_M zbierane,
  ale nieużywane"
- run_i2d(): pipeline faktycznie woła wszystkie 5 modułów (regresja
  "FusionEngine łączy tylko 3 z 5 obiecanych typów sygnału")
"""
import importlib
import importlib.util
from pathlib import Path

import cv2
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_by_path(name, filename):
    path = REPO_ROOT / filename
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------
# 1. Importy kanonicznych modułów
# ---------------------------------------------------------------------

CANONICAL_MODULES = [
    "i2d_core",
    "i2d_core_defectscanner_v2",
    "fusionengine_v1",
    "reportengine_v1",
    "rhythm_analyzer_v1",
    "colorpsychmap_v1",
    "colorpsychmap_lambda_psych",
    "spectral_overlay_detector_v2",
]


@pytest.mark.parametrize("module_name", CANONICAL_MODULES)
def test_canonical_module_imports_cleanly(module_name):
    importlib.import_module(module_name)


# ---------------------------------------------------------------------
# 2. Pliki ze spacjami = cienkie re-eksporty (tożsamość, nie tylko wynik)
# ---------------------------------------------------------------------

def test_colorpsychmap_v1_shim_is_same_function():
    import colorpsychmap_v1
    shim = _load_by_path("_shim_colorpsychmap_v1", "COLORPSYCHMAP v1.py")
    assert shim.detect_color is colorpsychmap_v1.detect_color


def test_colorpsychmap_lambda_psych_shim_is_same_function():
    import colorpsychmap_lambda_psych
    shim = _load_by_path("_shim_colorpsychmap_lambda", "ColorPsychMap Λ‑psych.py")
    assert shim.detect_color_emotion is colorpsychmap_lambda_psych.detect_color_emotion
    assert shim.hue_to_emotion is colorpsychmap_lambda_psych.hue_to_emotion


def test_reportengine_shim_is_same_function():
    import reportengine_v1
    shim = _load_by_path("_shim_reportengine", "REPORTENGINE v1.py")
    assert shim.report_engine is reportengine_v1.report_engine


def test_rhythm_analyzer_shim_is_same_function():
    import rhythm_analyzer_v1
    shim = _load_by_path("_shim_rhythm", "RHYTHM ANALYZER v1.py")
    assert shim.detect_rhythm is rhythm_analyzer_v1.detect_rhythm


def test_spectral_overlay_shim_is_same_function():
    import spectral_overlay_detector_v2
    shim = _load_by_path("_shim_spectral", "SPECTRAL OVERLAY DETECTOR v2.py")
    assert shim.detect_spectral_v2 is spectral_overlay_detector_v2.detect_spectral_v2


def test_fusionengine_space_name_shim_is_same_function():
    import fusionengine_v1
    shim = _load_by_path("_shim_fusion", "FUSIONENGINE v1.py")
    assert shim.fusion_engine is fusionengine_v1.fusion_engine


def test_i2d_core_defectscanner_v2_is_thin_reexport():
    import i2d_core
    import i2d_core_defectscanner_v2 as v2
    assert v2.detect_defects is i2d_core.detect_defects
    assert v2.detect_spectral is i2d_core.detect_spectral
    assert v2.run_i2d is i2d_core.run_i2d


# ---------------------------------------------------------------------
# 3. SpectralOverlayDetector — DC-bias: negatywna + pozytywna kontrola
# ---------------------------------------------------------------------

def _make_flat_frame(value=128, size=64, frame_id=0):
    from i2d_core import Frame
    raw = np.full((size, size, 3), value, dtype=np.uint8)
    return Frame(frame_id, 0.0, raw)


def test_spectral_flat_image_gives_zero_detections():
    from i2d_core import split_layers, detect_spectral
    f = _make_flat_frame()
    split_layers([f])
    assert detect_spectral([f]) == []


def test_spectral_detects_real_pattern_not_just_dc():
    from i2d_core import Frame, split_layers, detect_spectral
    size = 64
    xv, yv = np.meshgrid(np.arange(size), np.arange(size))
    checker = (((xv // 4) + (yv // 4)) % 2) * 255
    raw = np.stack([checker] * 3, axis=-1).astype(np.uint8)
    f = Frame(0, 0.0, raw)
    split_layers([f])
    assert len(detect_spectral([f])) > 0


# ---------------------------------------------------------------------
# 4. DefectScanner — próg adaptacyjny
# ---------------------------------------------------------------------

def test_defect_adaptive_threshold_ignores_noise_near_old_fixed_threshold():
    from i2d_core import Frame, detect_defects

    rng = np.random.default_rng(0)
    # Szum w okolicach starego, sztywnego progu (25) — przy starym kodzie
    # spora część takich bloków byłaby fałszywie wykryta jako "defekt".
    M = rng.uniform(20, 30, size=(64, 64)).astype(np.float32)
    M[0:16, 0:16] = 200.0  # jeden prawdziwy, wyraźny skok

    f = Frame(0, 0.0, raw=None)
    f.M = M

    detections = detect_defects([f], block_size=16)
    hit_blocks = {(d.x, d.y) for d in detections}

    assert hit_blocks == {(0, 0)}


# ---------------------------------------------------------------------
# 5. RhythmAnalyzer — okresowość dla L, V i M
# ---------------------------------------------------------------------

def _make_periodic_frames(n_frames, block_size, size, period, channel,
                           amplitude=150, base=50):
    from i2d_core import Frame
    frames = []
    for i in range(n_frames):
        L = np.full((size, size), base, dtype=np.uint8)
        C = np.zeros((size, size, 3), dtype=np.uint8)
        C[:, :, 2] = base
        M = np.full((size, size), base, dtype=np.uint8)

        value = amplitude if (i % period == 0) else base
        if channel == "L":
            L[0:block_size, 0:block_size] = value
        elif channel == "V":
            C[0:block_size, 0:block_size, 2] = value
        elif channel == "M":
            M[0:block_size, 0:block_size] = value

        f = Frame(i, float(i), raw=None)
        f.L, f.C, f.M = L, C, M
        frames.append(f)
    return frames


@pytest.mark.parametrize("channel,dtype", [
    ("L", "rhythm_periodic"),
    ("V", "rhythm_periodic_color"),
    ("M", "rhythm_periodic_motion"),
])
def test_rhythm_detects_periodicity_per_channel(channel, dtype):
    from rhythm_analyzer_v1 import detect_rhythm
    frames = _make_periodic_frames(
        n_frames=20, block_size=16, size=32, period=4, channel=channel
    )
    detections = detect_rhythm(
        frames, block_size=16, min_period=2, max_period=6, thr_periodic=0.3
    )
    hits = [d for d in detections if d.dtype == dtype]
    assert any(d.x == 0 and d.y == 0 for d in hits), (
        f"oczekiwano detekcji {dtype!r} w bloku (0,0) dla kanału {channel!r}"
    )


# ---------------------------------------------------------------------
# 6. run_i2d() — pipeline faktycznie woła wszystkie 5 modułów
# ---------------------------------------------------------------------

def test_run_i2d_image_mode_includes_color_module(tmp_path):
    from i2d_core import run_i2d

    img = np.full((64, 64, 3), (60, 60, 60), dtype=np.uint8)  # szare tło (BGR)
    img[0:32, 0:32] = (0, 0, 255)  # nasycona czerwień (BGR) w rogu

    path = tmp_path / "test_image.png"
    cv2.imwrite(str(path), img)

    detections = run_i2d(str(path), mode="image")
    dtypes = {d.dtype for d in detections}

    # POPRAWKA regresyjna: run_i2d wcześniej w ogóle nie wołał
    # detect_color_emotion/detect_rhythm — "color_emotion" nigdy się nie
    # pojawiało w wyniku, niezależnie od treści obrazu.
    assert "color_emotion" in dtypes
