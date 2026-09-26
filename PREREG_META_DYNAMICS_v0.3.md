# PREREG — META_DYNAMICS v0.3: ρ per region (UCSD Ped2)

Status: ZAMROŻONE i zacommitowane PRZED uruchomieniem bramki syntetycznej v0.3 i PRZED pobraniem klatek Test006–Test012.

## 0. Kontekst i jawność
- v0.1: ρ z globalnych Λ i E (próg mediana + 3,5·MAD) nie zadziałało ani razu — Λ i E klipów testowych nie
  przekraczały progów nawet w szczycie. v0.2: k = 2,0 bez marginesu na bramce syntetycznej → STOP.
- Diagnoza (eksploracja na zbiorze DEWELOPERSKIM: Train001–Train016 i Test001–Test005, wszystkie już oglądane w v0.1/v0.2
  lub przy kalibracji): klipy testowe są ogólnie bardziej ruchliwe niż referencja, więc prog globalny nie odróżnia
  „więcej pieszych” od „czegoś nietypowego w jednym miejscu”. Kamera Ped2 jest stała — każdy region ma własny typowy
  poziom ruchu.
- Projekt i k wybrano PO eksploracji danych deweloperskich. Autor widział zakresy `gt_frame` klipów Test006–Test012 w
  `UCSDped2.m` (tylko etykiety klatek, bez cech i wyników). Klatek Test006–Test012 nie pobierano.

## 1. Hipoteza
ρ per region oznacza klatki anomalne (gt) istotnie częściej niż klatki normalne na odłożonych klipach Test006–Test012.

## 2. Metoda (zamrożona, `meta_dynamics_v1.py`, sekcja v0.3)
- Energia ruchu regionu e_i(t) = średnia warstwy M w regionie siatki 4×4 (`region_energy_series`, bez zmian od v0.1).
- Referencja: Train001–Train012, energia liczona w każdym klipie osobno. Próg regionu: mediana_i + k·1,4826·MAD_i,
  MAD ≥ 1e-6.
- ρ(t) = 1, gdy e_i(t) > próg_i w którymkolwiek regionie. Dodatkowo zwracana mapa regionów (gdzie).
- k = 5,0 (`RHO_V3_K`).

## 3. Kalibracja k (zbiór deweloperski, `ped2_v03.py calibrate`)
Reguła: najmniejsze k z siatki {3,5; 4; 4,5; 5; 5,5; 6; 8}, dla którego fałszywe alarmy na Train013–Train016 ORAZ na
klatkach non-gt Test001–Test005 są ≤ 0,8·0,02 = 0,016 (margines — lekcja z v0.2). Wynik eksploracji (ta sama formuła):

| k | FA Train013–016 | FA non-gt Test001–005 | wykrycie gt Test001–005 |
| --- | --- | --- | --- |
| 4,0 | 0,029 | 0,048 | 0,772 |
| 4,5 | 0,019 | 0,019 | 0,735 |
| 5,0 | 0,016 | 0,010 | 0,702 |
| 5,5 | 0,011 | 0,005 | 0,677 |

→ k = 5,0. `ped2_v03.py calibrate` musi odtworzyć ten wybór przed oceną.

## 4. Bramka syntetyczna (`test_meta_dynamics_v03.py`) — STOP, jeśli którykolwiek test nie przejdzie
- Negatywna: czysty szum, 5 par ziaren (10/20, 98/99, 1000/1001, 2000/2001, 3000/3001): odsetek alarmów ≤ 0,075.
- Pozytywna: poruszający się jasny patch w oknie klatek 40–50, trzy przypadki (region (0,0), (2,3), (1,2)): wykrycie w
  oknie ≥ 0,5, alarmy poza oknem ≤ 0,075, w ≥ 80% oflagowanych klatek okna flaga wskazuje region wstrzyknięcia.

## 5. Ocena jednorazowa (`ped2_v03.py evaluate`) na Test006–Test012
Klatki gt wg `UCSDped2.m`. Uwaga: Test008–Test011 są w całości anomalne; klatki non-gt są tylko w Test006, Test007 i
Test012 (łącznie 153).
- (a) odsetek ρ = 1 na wszystkich klatkach gt ≥ 0,5;
- (b) odsetek ρ = 1 na wszystkich klatkach non-gt ≤ 0,10;
- (c) jednostronny dokładny test Fishera (gt > non-gt), p < 0,001;
- (d) w ≥ 5 z 7 klipów wykrycie gt ≥ max(0,3; 2 × FA z (b)).
SUPPORTED: wszystkie; NOT SUPPORTED: (c) nie spełnione; w pozostałych przypadkach PARTIALLY SUPPORTED.
Wynik raportowany w całości, bez dostrajania k po ocenie.

## 6. Ograniczenia (z góry)
Jedna scena i kamera (Ped2), ocena na poziomie klatek, nie obiektów; zbiór deweloperski był już oglądany; mała liczba
klatek non-gt w odłożonych klipach. ρ mówi „gdzie jest nietypowy ruch względem referencji”, nie „co to jest”.

## 7. Dane
Pełny UCSD Ped2 z mirrora `github.com/junaidwahid/UCSD-Anomaly-dataset` (commit c1d0517171d9d468f65a86baec834a29e63e42c5),
folder `UCSD_Anomaly_Dataset.v1p2/UCSDped2`, poza repo (`PED2_FULL`, domyślnie `../data/ucsd_ped2_full`).

## Aneks 1 (techniczny, przed jakimkolwiek wynikiem na Ped2 v0.3)
Pierwsze uruchomienie `ped2_v03.py calibrate` zostało zabite bez komunikatu (brak pamięci: 21 klipów z warstwami w RAM).
Dodano `region_reference_from_energies` i `rho_from_energies` (te same wzory, liczenie klip po klipie); `ped2_v03.py`
korzysta z nich. Bramka syntetyczna przeszła przed tą zmianą (10/10) i jest uruchamiana ponownie po niej. Wyników
kalibracji ani oceny nie oglądano.
