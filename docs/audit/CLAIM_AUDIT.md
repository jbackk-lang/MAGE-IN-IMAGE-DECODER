# Audyt twierdzeń: README → META_DYNAMICS, CONTOUR_CURVATURE, dashboard, CDnet, zdrowa referencja, testy (MAGE-IN-IMAGE-DECODER)

Silnik: claim_audit v0.2 (TIMDR-AI-Core).

Wygenerowano: 2026-09-26 13:16 UTC; reguły: `docs/audit/CLAIM_AUDIT_PREREG.md` (sha256 bf30d7610079), karty: `claims_mage.py` (sha256 bc903e75897e), README sha256 083596937efc.

Werdykty kart: DO ZŁAGODZENIA 1, NIEROZSTRZYGNIĘTE 2, POTWIERDZONE 21, SPRZECZNE 3.

## Twierdzenia

| # | Twierdzenie (cytat z README) | Werdykt | Przeliczenie | Uwagi |
| --- | --- | --- | --- | --- |
| M1 | na realnych danych tylko 1 z 3 klipów testowych dał istotny efekt na Λ, a binarna flaga ρ nie zadziałała w ogóle | POTWIERDZONE | istotne: ['Test002'] z ['Test001', 'Test002', 'Test003'] (α = 0,0083); ρ = 0 we wszystkich | SUROWE: real_meta_dynamics_ped2.py |
| M2 | (stała progowa `k=3.5` zdiagnozowana jako zbyt luźna) | SPRZECZNE | ρ nigdy = 1; maksima Λ/E poniżej progów (RESULT v0.1) | R12: próg nigdy nieprzekroczony = stała za wysoka (za surowa), nie „za luźna” |
| M3 | skalibrowało `k=2.0` na osobnym zbiorze (`data/ucsd_ped2_calibration/`, rozłącznym z Test001-003) | POTWIERDZONE | wybrane k = 2.0; klipy kalibracyjne ['Test004', 'Test005'] | SUROWE: calibrate_rho_threshold.py |
| M4 | `k=2.0` nie ma bezpiecznego marginesu — na innym scenariuszu syntetycznym niż ten użyty w kalibracji fałszywy alarm wychodzi dokładnie na granicy progu | POTWIERDZONE | test dokumentujący fałszywy alarm = 0,150 przy bramce < 0,15 przechodzi | KOD REPO |
| M5 | Zgodnie z protokołem stop-if-failed, `Test001-003` NIE zostały ponownie dotknięte | NIEROZSTRZYGNIĘTE | skrypt Test001-003 bez k = 2,0; zapis w RESULT v0.2 | DOKUMENT + KOD |
| M6 | Λ pozostaje częściowym tropem (1 z 3 klipów, niepotwierdzone) | POTWIERDZONE | 1 z 3 |  |
| M7 | Dashboard pokazuje historyczne `rho` wyłącznie informacyjnie; nie używa go jako zwalidowanego alarmu | POTWIERDZONE | app.py: „historyczne rho … (NIE jest alarmem)” | KOD |
| C1 | sekcja 0 | POTWIERDZONE | sekcja 0 w PREREG |  |
| C2 | **CZĘŚCIOWO SUPPORTED, niska moc (N=4)**: bramka syntetyczna przeszła czysto (7/7 testów), ale na realnych danych tylko 1 z 4 obrazów dał istotny efekt (po korekcie Bonferroniego) | POTWIERDZONE | istotne 1 z 4 (['Tp_S_NRN_S_N_pla00005_pla00005_10937']); testy syntetyczne 7 | SUROWE: real_contour_curvature_casia2.py |
| C3 | jedyny publicznie dostępny podzbiór CASIA v2 z ground truth ma tylko 4 przykłady (oryginalny zbiór nie jest już hostowany publicznie) | NIEROZSTRZYGNIĘTE | w repo 4 obrazy z maskami | „jedyny publicznie dostępny” i „nie jest już hostowany” - twierdzenia o świecie, nieweryfikowalne z plików |
| D1 | Otwiera się na `http://localhost:5050` | POTWIERDZONE | port 5050 | KOD |
| D2 | Strona per moduł (wszystkie 7: 5 stabilnych detektorów + META_DYNAMICS + CONTOUR_CURVATURE) | POTWIERDZONE | MODULES: 5 stabilnych + 2 eksperymentalne | KOD |
| D3 | Wgrywane wideo ma limit 300 klatek, 12 mln pikseli łącznie i 20 MB; zbyt duży plik jest odrzucany jawnie, a nie po cichu obcinany | POTWIERDZONE | 300 klatek, 12 mln pikseli, 20 MB; load_video rzuca błąd zamiast obcinać | KOD |
| L0 | `cdnet_benchmark.py` porównuje na tych samych klatkach trzy maski | SPRZECZNE | METHODS w cdnet_benchmark.py: 10 masek | KOD |
| L1 | ### Laboratorium porównań CDnet 2014 | POTWIERDZONE | zbiór CDnet 2014 (changedetection.net/dataset2014) |  |
| L2 | piksele z etykietami 0 (tło) lub 255 (ruch), wewnątrz `ROI.bmp`; etykiety 50, 85 i 170 są pomijane | POTWIERDZONE | etykiety oceniane [0, 255], pomijane [50, 85, 170] | JSON + KOD |
| L3 | W tym pilotażu fuzja nie poprawiła wyniku względem pojedynczego detektora | DO ZŁAGODZENIA | pedestrians: fuzja − DefectScanner = -0.0195; fountain01: fuzja − DefectScanner = +0.0006 | R10: F1 fuzji wyższy na co najmniej jednej sekwencji (SUROWE, F1 = raport) |
| L4 | MOG2 połączony z kierunkowo spójnym ruchem poprawił F1 na obu sekwencjach, lecz był ok. 5–6× wolniejszy od MOG2 | POTWIERDZONE | F1 = raport: True; stosunek czasu 5,5× i 4,5× | R8, R9 |
| L5 | Sprawdzenie bez zmian progów na dwóch nowych sekwencjach | POTWIERDZONE | parametry raportów identyczne; highway/canoe nieużyte wcześniej | JSON |
| L6 | F1 rośnie na `highway` i `canoe`, ale metoda nadal jest 3.8–4.0× wolniejsza od MOG2 | POTWIERDZONE | F1 = raport: True; stosunek czasu 4,6× i 4,0× | R8, R9 |
| L7 | przeliczanie pola co 2 klatki zachowuje prawie cały F1 pełnej fuzji przy około 1.6× krótszym czasie; rzadki LK w ROI wyraźnie traci recall | POTWIERDZONE | F1 = raport: True; co 2 klatki zachowuje F1: True; LK traci recall: True; przyspieszenie 1,64× i 1,59× | R8, R9, R11 |
| V1 | medianą i 90. percentylem jego długości | POTWIERDZONE | percentyl 90 długości wektorów | KOD |
| V2 | Na pierwszych 60% zdrowych par kalibruje medianę/MAD, a na pozostałych 40% próg kontrolny | POTWIERDZONE | podział 0,6 / 0,4 | KOD; kod wymusza też co najmniej 12 par kalibracyjnych (max(12, …)), więc dla krótkich filmów podział nie jest dokładnie 60/40 |
| T1 | 22 testy: import każdego modułu | SPRZECZNE | `pytest tests/`: 45 testów (w tym 22 w test_i2d_core.py) | R14 |
| T2 | 11 testów dla META_DYNAMICS v0.1/v0.2 (`test_meta_dynamics_v1.py` — kontrole syntetyczne k=3.5 i k=2.0 | POTWIERDZONE | 11 testów | R14 |
| T3 | 7 testów dla CONTOUR_CURVATURE v0.1 | POTWIERDZONE | 7 testów | R14 |
| T4 | (N=4, za mało na sensowną regresję automatyczną) | POTWIERDZONE | 4 obrazy |  |

## Reguły całego fragmentu

| Reguła | Wynik | Szczegóły |
| --- | --- | --- |
| R5 kompletność | POTWIERDZONE | RESULT v0.2: ρ NOT SUPPORTED - README to podaje |
| R5 kompletność | POTWIERDZONE | RESULT CONTOUR: częściowo - README to podaje |
| R6 kotwica | NIEROZSTRZYGNIĘTE | PREREG_META_DYNAMICS_v0.1.md i RESULT_META_DYNAMICS_v0.1.md w tym samym lub pozniejszym commicie (237ea44 / 237ea44) - zamrozenie tylko deklarowane |
| R6 kotwica | NIEROZSTRZYGNIĘTE | PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md i RESULT_META_DYNAMICS_v0.2.md w tym samym lub pozniejszym commicie (1231ba9 / 1231ba9) - zamrozenie tylko deklarowane |
| R6 kotwica | NIEROZSTRZYGNIĘTE | PREREG_META_DYNAMICS_v0.2.md i RESULT_META_DYNAMICS_v0.2.md w tym samym lub pozniejszym commicie (1231ba9 / 1231ba9) - zamrozenie tylko deklarowane |
| R6 kotwica | NIEROZSTRZYGNIĘTE | PREREG_CONTOUR_CURVATURE_v0.1.md i RESULT_CONTOUR_CURVATURE_v0.1.md w tym samym lub pozniejszym commicie (d834089 / d834089) - zamrozenie tylko deklarowane |
| R7b sformułowanie | DO ZŁAGODZENIA | „dowodzi”: „dowodzi” wymaga dowodu |

## Analiza (po uruchomieniu, post hoc — karty i reguły NIE zostały zmienione)

**Wyniki odtwarzają się z danych.** META_DYNAMICS na Ped2: istotny tylko Test002 (p = 9,9·10⁻²²), ρ = 0 wszędzie;
kalibracja wybiera k = 2,0 na Test004–005; CONTOUR: 1 z 4 obrazów CASIA (p = 0,0014); 63 testy przechodzą. CDnet:
wszystkie cztery sekwencje przeliczone od surowych klatek (pedestrians i canoe na urządzeniu, fountain01 i highway w chmurze
— na urządzeniu przekraczały limit czasu; ta sama wersja OpenCV 5.0.0.93) — **F1 wszystkich metod równe raportom do
4 miejsc**. Stosunki czasu w powtórce: MOG2 ∩ wektory 5,5× i 4,5× wolniejsze od MOG2 (README: 5–6×), 4,6× i 4,0×
(README: 3,8–4,0×), pole co 2 klatki 1,64× i 1,59× szybsze (README: ~1,6×) — w tolerancji R9, ale czasy zależą od
maszyny (fountain01/highway liczone równolegle w chmurze).

**Co jest nieaktualne albo źle sformułowane:**
- **M2 „k = 3,5 … zbyt luźna”** — ρ nigdy nie zadziałało, bo Λ i E nie przekraczały progu nawet w szczycie (RESULT v0.1).
  Stała jest więc zbyt WYSOKA (za surowa), nie luźna; to samo słowo jest w RESULT v0.1.
- **L0 „porównuje trzy maski”** — `cdnet_benchmark.py` liczy dziś 10 masek (3 bazowe + 7 wariantów z polem wektorów).
- **L3 „fuzja nie poprawiła wyniku”** — na fountain01 F1 fuzji jest wyższy o 0,0006 (pomijalnie), na pedestrians niższy
  o 0,0195. Sformułowanie bezwzględne; różnica bez znaczenia praktycznego.
- **T1 „22 testy”** (`pytest tests/`) — dziś 45: 22 w `test_i2d_core.py` + 23 w nowszych plikach (podobieństwo, CDnet,
  fuzja/diagnostyka, stereo, zdrowa referencja).
- **R6** — wszystkie cztery pre-rejestracje (META v0.1, kalibracja, META v0.2, CONTOUR) są w tych samych commitach co
  wyniki; README tego nie mówi.

**Błędy/ograniczenia kart:** M5 — karta szukała „2.0” w skrypcie i trafiła na wzór efektu rank-biserial; historia gita
nie pokazuje żadnej zmiany wyników/skryptu Test001–003 po commicie v0.2 (1231ba9), co wspiera twierdzenie, ale jest to
nadal dowód z dokumentu. R7b „dowodzi” — fałszywy alarm (zdanie jest zaprzeczone: „nie dowodzi przewagi”).
C3 — dostępność CASIA v2 w internecie nie jest sprawdzalna z plików.
