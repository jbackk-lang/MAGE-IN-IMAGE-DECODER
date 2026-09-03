"""
i2d_core_defectscanner_v2.py — kompatybilność wsteczna.

POPRAWKA: ten plik był niezależną kopią i2d_core.py, która się z nim
rozjechała — m.in. detect_defects() miał tu próg adaptacyjny
(mean(M) + 2*std(M)), którego brakowało w i2d_core.py (tam był sztywny
próg 25), a detect_spectral() unikał tu sekcji "ring" zamiast naprawić
przyczynę (dominację składowej DC), więc nadal fałszywie zgłaszał
spectral_anomaly na centralnym bloku. Obie te rozbieżności są teraz
naprawione w i2d_core.py (detect_defects ma próg adaptacyjny,
detect_spectral deleguje do spectral_overlay_detector_v2.py, które
poprawnie wyklucza DC) — ten plik jest cienkim re-eksportem, żeby
istniejący kod importujący z i2d_core_defectscanner_v2 dalej działał
bez zmian, ale bez ryzyka, że te dwa moduły znów się rozjadą.

Użycie (bez zmian):
    from i2d_core_defectscanner_v2 import run_i2d, Frame, Detection
"""
from i2d_core import (
    Frame,
    Detection,
    load_video,
    load_image,
    split_layers,
    detect_twist,
    detect_defects,
    detect_spectral,
    run_i2d,
)
