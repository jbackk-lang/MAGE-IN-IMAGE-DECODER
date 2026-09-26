# Audyt twierdzeń README — MAGE-IN-IMAGE-DECODER — pre-rejestracja

Status: ZAMROŻONE i zacommitowane PRZED pierwszym uruchomieniem przeliczeń i audytu. Silnik: `tools/claim_audit.py`
(TIMDR-AI-Core `claim_audit` v0.2), reguły ogólne R1–R7 jak w `TIMDR-AI-Core/CLAIM_AUDIT.md`. Audytor przeczytał README,
pliki PREREG_*/RESULT_*, raporty `benchmark_reports/*.json` (poza gitem) i kod przed napisaniem kart; nie uruchamiał
skryptów wynikowych.

## Zakres
README.md: „### META_DYNAMICS v0.1” i „### CONTOUR_CURVATURE v0.1” (do pierwszego bloku kodu), „## 🖥️ Dashboard”
(do „### Szybkie nakładki stereo”), „### Laboratorium porównań CDnet 2014”, „### Film względem zdrowej referencji”,
„## 🧪 Testy”. Moduły stabilne i sekcja „Zastosowania” poza zakresem.

## Poziomy dowodu
SUROWE (ponowne uruchomienie skryptów repo na danych: `real_meta_dynamics_ped2.py`, `calibrate_rho_threshold.py`,
`real_contour_curvature_casia2.py`, `cdnet_benchmark.py` na pełnych sekwencjach CDnet z `../data/cdnet2014`), JSON
(raporty `benchmark_reports/`), KOD (stałe i ścieżki w źródle), DOKUMENT (PREREG/RESULT), ŚWIAT (twierdzenia o dostępności
zbiorów w internecie — NIEROZSTRZYGNIĘTE).

## Reguły dodatkowe
- R8 F1 z ponownego uruchomienia musi być równe raportowi JSON do 4 miejsc po przecinku (obliczenia deterministyczne).
- R9 Stosunki czasu („N× wolniejszy”) liczone z czasów na klatkę z ponownego uruchomienia; zakres z README przechodzi, gdy
  obserwowany stosunek leży w [0,85·a; 1,15·b]. Czasy z raportów JSON podawane opisowo (inna maszyna/obciążenie).
- R10 „fuzja nie poprawiła wyniku”: jakikolwiek wzrost F1 fuzji nad pojedynczym detektorem na którejkolwiek sekwencji →
  DO ZŁAGODZENIA (twierdzenie bezwzględne), spadek/równość na wszystkich → POTWIERDZONE.
- R11 „prawie cały F1”: F1 wariantu ≥ 0,98 × F1 pełnej fuzji; „wyraźnie traci recall”: recall ≤ 0,6 × recall pełnej fuzji.
- R12 „zbyt luźna” (stała progowa): jeśli flaga nigdy nie zadziałała, a maksima Λ/E są poniżej progów, stała jest zbyt
  WYSOKA (za surowa), a nie luźna → SPRZECZNE (sformułowanie odwrotne do diagnozy).
- R13 „istotny efekt”: Λ — Mann–Whitney p < α_corr z pliku skryptu (Bonferroni); CASIA — p < 0,0125.
- R14 Liczby testów: zliczane przez `pytest --collect-only` dla wskazanych plików/katalogu.
- R6 kotwice: każda para PREREG/RESULT (META v0.1, v0.2, kalibracja, CONTOUR).
