# Audyt twierdzeń: README → META_DYNAMICS, CONTOUR_CURVATURE, dashboard, CDnet, zdrowa referencja, testy (MAGE-IN-IMAGE-DECODER)

Silnik: claim_audit v0.2 (TIMDR-AI-Core).

Drugi przebieg, po poprawkach README (`CLAIM_AUDIT_ADDENDUM_1.md`). Pierwszy przebieg z analizą: `CLAIM_AUDIT_v1.md`. Karty zmieniono po pierwszym przebiegu — ten raport sprawdza zgodność poprawionego README z plikami, nie jest niezależnym testem.

Wygenerowano: 2026-09-26 13:18 UTC; reguły: `docs/audit/CLAIM_AUDIT_PREREG.md` (sha256 bf30d7610079), karty: `claims_mage.py` (sha256 a4f5dad2bd7e), README sha256 51a88c633054.

Werdykty kart: NIEROZSTRZYGNIĘTE 1, POTWIERDZONE 30, UDOKUMENTOWANE 1.

## Twierdzenia

| # | Twierdzenie (cytat z README) | Werdykt | Przeliczenie | Uwagi |
| --- | --- | --- | --- | --- |
| M1 | na realnych danych tylko 1 z 3 klipów testowych dał istotny efekt na Λ, a binarna flaga ρ nie zadziałała w ogóle | POTWIERDZONE | istotne: ['Test002'] z ['Test001', 'Test002', 'Test003'] (α = 0,0083); ρ = 0 we wszystkich | SUROWE: real_meta_dynamics_ped2.py |
| M2 | (stała progowa `k=3.5` okazała się zbyt wysoka - Λ i E nie przekroczyły progu nawet w szczycie, więc flaga nie miała szansy zadziałać) | POTWIERDZONE | ρ nigdy = 1; maksima Λ/E poniżej progów (RESULT v0.1) | R12 |
| M3 | skalibrowało `k=2.0` na osobnym zbiorze (`data/ucsd_ped2_calibration/`, rozłącznym z Test001-003) | POTWIERDZONE | wybrane k = 2.0; klipy kalibracyjne ['Test004', 'Test005'] | SUROWE: calibrate_rho_threshold.py |
| M4 | `k=2.0` nie ma bezpiecznego marginesu — na innym scenariuszu syntetycznym niż ten użyty w kalibracji fałszywy alarm wychodzi dokładnie na granicy progu | POTWIERDZONE | test dokumentujący fałszywy alarm = 0,150 przy bramce < 0,15 przechodzi | KOD REPO |
| M5 | Zgodnie z protokołem stop-if-failed, `Test001-003` NIE zostały ponownie dotknięte | UDOKUMENTOWANE | zmiany po v0.2 (1231ba9) w plikach Test001-003: ['ad1e18b'] (tylko erratum) | DOKUMENT + historia gita |
| M6 | Λ pozostaje częściowym tropem (1 z 3 klipów, niepotwierdzone) | POTWIERDZONE | 1 z 3 |  |
| M7 | Dashboard pokazuje historyczne `rho` wyłącznie informacyjnie; nie używa go jako zwalidowanego alarmu | POTWIERDZONE | app.py: „historyczne rho … (NIE jest alarmem)” | KOD |
| C1 | sekcja 0 | POTWIERDZONE | sekcja 0 w PREREG |  |
| C2 | **CZĘŚCIOWO SUPPORTED, niska moc (N=4)**: bramka syntetyczna przeszła czysto (7/7 testów), ale na realnych danych tylko 1 z 4 obrazów dał istotny efekt (po korekcie Bonferroniego) | POTWIERDZONE | istotne 1 z 4 (['Tp_S_NRN_S_N_pla00005_pla00005_10937']); testy syntetyczne 7 | SUROWE: real_contour_curvature_casia2.py |
| C3 | jedyny publicznie dostępny podzbiór CASIA v2 z ground truth ma tylko 4 przykłady (oryginalny zbiór nie jest już hostowany publicznie) | NIEROZSTRZYGNIĘTE | w repo 4 obrazy z maskami | „jedyny publicznie dostępny” i „nie jest już hostowany” - twierdzenia o świecie, nieweryfikowalne z plików |
| D1 | Otwiera się na `http://localhost:5050` | POTWIERDZONE | port 5050 | KOD |
| D2 | Strona per moduł (wszystkie 7: 5 stabilnych detektorów + META_DYNAMICS + CONTOUR_CURVATURE) | POTWIERDZONE | MODULES: 5 stabilnych + 2 eksperymentalne | KOD |
| D3 | Wgrywane wideo ma limit 300 klatek, 12 mln pikseli łącznie i 20 MB; zbyt duży plik jest odrzucany jawnie, a nie po cichu obcinany | POTWIERDZONE | 300 klatek, 12 mln pikseli, 20 MB; load_video rzuca błąd zamiast obcinać | KOD |
| L0 | `cdnet_benchmark.py` porównuje na tych samych klatkach 10 masek: trzy bazowe | POTWIERDZONE | METHODS: 10 | KOD |
| L8 | i 7 wariantów z polem wektorów ruchu | POTWIERDZONE | METHODS: 10 | KOD |
| L1 | ### Laboratorium porównań CDnet 2014 | POTWIERDZONE | zbiór CDnet 2014 (changedetection.net/dataset2014) |  |
| L2 | piksele z etykietami 0 (tło) lub 255 (ruch), wewnątrz `ROI.bmp`; etykiety 50, 85 i 170 są pomijane | POTWIERDZONE | etykiety oceniane [0, 255], pomijane [50, 85, 170] | JSON + KOD |
| L3 | W tym pilotażu fuzja nie poprawiła wyniku w praktycznym sensie względem pojedynczego detektora (F1: pedestrians −0.020, fountain01 +0.001) | POTWIERDZONE | pedestrians: -0.0195; fountain01: +0.0006 | SUROWE |
| L4 | MOG2 połączony z kierunkowo spójnym ruchem poprawił F1 na obu sekwencjach, lecz był ok. 5–6× wolniejszy od MOG2 | POTWIERDZONE | F1 = raport: True; stosunek czasu 5,5× i 4,5× | R8, R9 |
| L4b | (czasy zależą od maszyny; w powtórce audytu 4.5–5.5×) | POTWIERDZONE | 5,55× i 4,47× | powtórka audytu |
| L5 | Sprawdzenie bez zmian progów na dwóch nowych sekwencjach | POTWIERDZONE | parametry raportów identyczne; highway/canoe nieużyte wcześniej | JSON |
| L6 | F1 rośnie na `highway` i `canoe`, ale metoda nadal jest 3.8–4.0× wolniejsza od MOG2 | POTWIERDZONE | F1 = raport: True; stosunek czasu 4,6× i 4,0× | R8, R9 |
| L6b | (w powtórce audytu 4.0–4.6×) | POTWIERDZONE | 4,59× i 3,96× | powtórka audytu |
| L9 | F1 wszystkich raportów CDnet odtwarza się co do 4 miejsc przy ponownym uruchomieniu na surowych klatkach | POTWIERDZONE | raporty: 7; różnice F1: brak | R8 |
| L7 | przeliczanie pola co 2 klatki zachowuje prawie cały F1 pełnej fuzji przy około 1.6× krótszym czasie; rzadki LK w ROI wyraźnie traci recall | POTWIERDZONE | F1 = raport: True; co 2 klatki zachowuje F1: True; LK traci recall: True; przyspieszenie 1,64× i 1,59× | R8, R9, R11 |
| V1 | medianą i 90. percentylem jego długości | POTWIERDZONE | percentyl 90 długości wektorów | KOD |
| V2 | Na pierwszych 60% zdrowych par kalibruje medianę/MAD, a na pozostałych 40% próg kontrolny | POTWIERDZONE | podział 0,6 / 0,4 | KOD; kod wymusza też co najmniej 12 par kalibracyjnych (max(12, …)), więc dla krótkich filmów podział nie jest dokładnie 60/40 |
| T1 | 45 testów, w tym 22 w `tests/test_i2d_core.py`: import każdego modułu | POTWIERDZONE | 45 testów, 22 w test_i2d_core.py | R14 |
| T5 | pozostałe 23 dotyczą podobieństwa, CDnet, fuzji/diagnostyki, nakładek stereo i zdrowej referencji | POTWIERDZONE | 23 pozostałych | R14 |
| T2 | 11 testów dla META_DYNAMICS v0.1/v0.2 (`test_meta_dynamics_v1.py` — kontrole syntetyczne k=3.5 i k=2.0 | POTWIERDZONE | 11 testów | R14 |
| T3 | 7 testów dla CONTOUR_CURVATURE v0.1 | POTWIERDZONE | 7 testów | R14 |
| T4 | (N=4, za mało na sensowną regresję automatyczną) | POTWIERDZONE | 4 obrazy |  |

## Reguły całego fragmentu

| Reguła | Wynik | Szczegóły |
| --- | --- | --- |
| R5 kompletność | POTWIERDZONE | RESULT v0.2: ρ NOT SUPPORTED - README to podaje |
| R5 kompletność | POTWIERDZONE | RESULT CONTOUR: częściowo - README to podaje |
| R6 kotwica | UJAWNIONE | PREREG_META_DYNAMICS_v0.1.md i RESULT_META_DYNAMICS_v0.1.md w tym samym commicie (237ea44 / 237ea44); README opisuje to ograniczenie |
| R6 kotwica | UJAWNIONE | PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md i RESULT_META_DYNAMICS_v0.2.md w tym samym commicie (1231ba9 / 1231ba9); README opisuje to ograniczenie |
| R6 kotwica | UJAWNIONE | PREREG_META_DYNAMICS_v0.2.md i RESULT_META_DYNAMICS_v0.2.md w tym samym commicie (1231ba9 / 1231ba9); README opisuje to ograniczenie |
| R6 kotwica | UJAWNIONE | PREREG_CONTOUR_CURVATURE_v0.1.md i RESULT_CONTOUR_CURVATURE_v0.1.md w tym samym commicie (d834089 / d834089); README opisuje to ograniczenie |
