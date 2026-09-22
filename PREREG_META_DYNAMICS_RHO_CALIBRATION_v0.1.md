# PREREG — Kalibracja progu ρ (META_DYNAMICS, wideo)

Status: ZAMROŻONE PRZED uruchomieniem sweepu `k`. Cel, siatka
kandydacka i REGUŁA WYBORU `k` poniżej nie mogą się zmienić po
zobaczeniu wyników sweepu. Osobny dokument od `PREREG_META_DYNAMICS_v0.1.md`
— tamten zamraża WZORY (Λ/τ/ρ), ten zamraża TYLKO wartość stałej `k` w
`ρ(t) = 1 jeśli Λ(t) > mediana+k·MAD LUB E(t) > mediana+k·MAD`.

## 1. Powód

`RESULT_META_DYNAMICS_v0.1.md` udokumentował, że `k=3.5` (stała
przeniesiona bez zmian z domeny wibracji/sejsmiki, patrz `ROBUST_K` w
całym ekosystemie TIMDR) nigdy nie wyzwala ρ na danych wideo UCSD Ped2 —
wartości Λ/E na danych testowych nie przekraczają progu nawet w
szczycie. To nie jest błąd kodu — to miskalibracja stałej międzydomenowej.

## 2. Zbiór kalibracyjny — ROZŁĄCZNY z głównym testem

- **Referencja (zdrowa)**: te same `Train001-004` co w v0.1 (niezmienione
  — kalibracja progu nie wymaga nowej referencji, tylko nowego `k`).
- **Kalibracja**: `Test004`, `Test005` (NOWE klipy, `data/ucsd_ped2_calibration/`)
  — WYŁĄCZNIE do tego dokumentu. `Test001-003` (główny test v0.1) NIE są
  dotykane w tym etapie — pozostają w pełni odseparowane, żeby druga
  runda testu głównego (v0.2) nie była oceniana na danych, na których
  dobrano próg (wyciek danych unieważniłby test).
- **Kontrola negatywna**: świeża syntetyczna sekwencja szumu, NOWY seed
  (`seed=99`), nieużywany w żadnym teście `test_meta_dynamics_v1.py` do
  tej pory — żeby nie dobierać `k` pod jeden konkretny, już widziany
  szum.

## 3. Siatka kandydacka `k`

`k ∈ {3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.75, 0.5}` (malejąco od oryginalnej
wartości ekosystemu TIMDR w dół — szukamy NAJMNIEJSZEGO odejścia od
konwencji, które faktycznie działa, nie najbardziej czułego możliwego
progu).

## 4. Metryki na kandydata `k` (liczone RAZ, dla każdego `k` osobno)

- `false_alarm_rate(k)` — odsetek klatek z ρ=1 na świeżej syntetycznej
  kontroli negatywnej (60 klatek szumu, `seed=99`, referencja z osobnych
  30 klatek `seed=98`).
- `calib_sensitivity(k)` — odsetek klatek z ρ=1 WEWNĄTRZ `gt_frame` na
  Test004+Test005 łącznie (pula klatek obu klipów).
- `calib_non_gt_rate(k)` — odsetek klatek z ρ=1 POZA `gt_frame` na
  Test004+Test005 łącznie.

## 5. Reguła wyboru `k` (zamrożona, deterministyczna)

Wybierz **największe** `k` z siatki (sekcja 3) spełniające WSZYSTKIE:

1. `false_alarm_rate(k) < 0.15` (ta sama bramka co kontrola negatywna w
   `PREREG_META_DYNAMICS_v0.1.md` sekcja 4),
2. `calib_sensitivity(k) >= 0.10` (ρ faktycznie wykrywa choć część
   anomalii — nie jest martwe jak przy k=3.5),
3. `calib_sensitivity(k) > calib_non_gt_rate(k)` (dyskryminuje, nie tylko
   "włącza się wszędzie").

Jeśli ŻADNE `k` z siatki nie spełnia wszystkich trzech — kalibracja
KOŃCZY SIĘ NEGATYWNIE: ρ w obecnej definicji (mediana+k·MAD na Λ/E) nie
daje się uratować prostym doborem progu w tym zakresie, i to jest
kompletny, uczciwy wynik tego dokumentu (nie powód do rozszerzania
siatki post-hoc).

## 6. Co dzieje się z wybranym `k`

Wybrane `k` staje się wejściem do **v0.2** (`PREREG_META_DYNAMICS_v0.2.md`,
o ile kalibracja się powiedzie) — druga runda TEGO SAMEGO protokołu co
v0.1 (bramka syntetyczna z nowym `k` → test na `Test001-003`, nietkniętych
w tym etapie). Λ i τ (nie zależą od `k`) pozostają bez zmian względem
v0.1. `k` NIE jest dalej dostrajane po tym etapie — jeśli v0.2 na
`Test001-003` da wynik rozczarowujący, to jest wynik v0.2, nie powód do
powrotu i przekalibrowania `k` po raz drugi.
