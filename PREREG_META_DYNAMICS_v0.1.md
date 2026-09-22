# PREREG — META_DYNAMICS_v0.1 (Λ/τ/ρ na siatce regionów ruchu)

Status: ZAMROŻONE PRZED dotknięciem realnych danych UCSD Ped2 (poniżej —
sekcja "Dane referencyjne i testowe"). Wzory, progi i plan testu
statystycznego nie mogą się zmienić po zobaczeniu wyniku na danych
realnych — ewentualna zmiana metodologii po zobaczeniu wyniku wymaga
nowej wersji (v0.2) z osobnym PREREG, nie retuningu tego dokumentu.
Protokół zgodny z `timdr-signal-framework` (anti-numerologia: kontrole
syntetyczne przed danymi realnymi, test istotności + rozmiar efektu,
uczciwe zgłoszenie wyniku negatywnego).

## 1. Cel i pytanie testowalne

Czy stan meta-dynamiki (Λ = koncentracja przestrzenna ruchu, τ = tempo
zmiany globalnej energii ruchu, ρ = anomalia względem referencji zdrowej)
policzony na klatkę wideo pozwala odróżnić klatki oznaczone jako anomalne
(`gt_frame`, UCSD Ped2) od klatek normalnych W TYM SAMYM klipie testowym.

To NIE jest twierdzenie, że przewyższa istniejące metody detekcji
anomalii wideo (te są dobrze rozwinięte, patrz zastrzeżenie w rozmowie
poprzedzającej ten dokument) — to test, czy przeniesienie formalizmu
Λ-τ-ρ (już zwalidowanego na sygnałach 1D w GIA-TIMDR/TIMDR-Industrial-Predict)
na pole ruchu wideo daje SENSOWNY, nietrywialny sygnał, zanim zainwestujemy
dalej w tę gałąź.

## 2. Ekstrakcja sygnału (na klatkę)

Wykorzystuje ISTNIEJĄCĄ infrastrukturę repo: `Frame.M` z `split_layers()`
(różnica bezwzględna jasności klatka-do-klatki, `cv2.absdiff`) — nie
duplikujemy logiki wczytywania/warstw.

**Siatka regionów**: klatka dzielona na `grid=(4,4)` (16 regionów) —
domyślnie, parametryzowalne. Dla klatek Ped2 (240×360) daje to regiony
~60×90 px.

**Wektor energii regionów** `e(t) ∈ ℝ¹⁶`: `e_i(t) = mean(M[region_i])`
dla klatki `t` (średnia wartość różnicy bezwzględnej w regionie `i`).

## 3. Wzory Λ / τ / ρ (zamrożone)

**Λ(t) — koncentracja przestrzenna** (entropijna, nie widmowa w sensie
FFT — "widmo" tu znaczy rozkład energii MIĘDZY regionami, nie
częstotliwości):

```
p_i(t) = e_i(t) / Σe(t)          (jeśli Σe(t) ≈ 0: p = rozkład jednostajny)
H(t)   = -Σ p_i(t)·ln(p_i(t))     (entropia Shannona, pomijając p_i=0)
H_max  = ln(liczba_regionów)
Λ(t)   = clip(1 - H(t)/H_max, 0, 1)
```

Λ≈0: ruch rozłożony równomiernie po scenie (np. wielu pieszych albo brak
ruchu → rozkład jednostajny domyślny). Λ≈1: ruch skupiony w
jednym/kilku regionach.

**τ(t) — tempo zmiany globalnej energii ruchu**: `E(t) = Σe(t)`
(całkowita energia ruchu w klatce). `τ(t)` = nachylenie regresji liniowej
najmniejszych kwadratów `E` względem indeksu klatki w oknie
`[t-w, t+w]`, `w=4` (9 klatek), przycinane na brzegach sekwencji. Klatki
wideo są z definicji równoodległe w indeksie — NIE używamy tu
zmiennoczasowego sąsiedztwa `_nearest_k_bounds` z TIMDR_EarthquakeCore
(to jest uproszczenie świadome, nie przeoczenie: ten mechanizm istnieje w
oryginale dla nierównomiernego próbkowania sejsmicznego/telemetrii,
którego tu nie ma).

**ρ(t) — anomalia względem referencji zdrowej** (MAD-owa, konwencja
całego ekosystemu TIMDR — `mediana + k·MAD`, `k=3.5`, ta sama stała co w
`bearing_meta_adapter.py`/`TIMDR-Earthquake-Core`, NIE dostrajana pod to
zadanie):

```
próg_Λ = mediana(Λ_ref) + 3.5·MAD(Λ_ref)
próg_E = mediana(E_ref) + 3.5·MAD(E_ref)
ρ(t) = 1  jeśli Λ(t) > próg_Λ  LUB  E(t) > próg_E,  inaczej 0
```

gdzie `Λ_ref`/`E_ref` policzone WYŁĄCZNIE z klipów TRENINGOWYCH (zdrowych)
— nigdy z klipów testowych, zgodnie z oficjalnym protokołem Ped2 (klipy
treningowe zawierają WYŁĄCZNIE normalne klatki, patrz README datasetu).

**J (operator skrętu/punktowy) — ŚWIADOMIE POMINIĘTY w v0.1.** Repo ma
już własny `TwistDetector` (asymetria przestrzenna L/R, góra/dół w
bloku) o INNEJ definicji niż `J` z TIMDR-META-DYNAMICS (tam: częstość
przekroczenia progu na pochodnej `flow_grad`) — żeby uniknąć kolizji
nazw/znaczeń w tym samym repo, `J` zostaje poza zakresem v0.1. Jeśli w
v0.2 okaże się potrzebny, dostanie osobną nazwę (nie "twist").

## 4. Kontrole syntetyczne (WYMAGANE przed danymi realnymi)

**Kontrola pozytywna**: 60 klatek syntetycznych, szare tło + szum
gaussowski (referencja = klatki 0-29, "zdrowe"), potem wstrzyknięty
lokalny jasny, poruszający się patch W JEDNYM regionie siatki w oknie
klatek 40-50. Oczekiwane: Λ(t) i ρ(t) wyraźnie podwyższone w oknie
40-50 względem referencji.

**Kontrola negatywna**: analogiczna sekwencja 60 klatek szumu, BEZ
wstrzyknięcia, inny seed niż referencja. Oczekiwane: ρ(t)==0 dla
zdecydowanej większości klatek (brak spurious alarmów).

**Bramka**: obie kontrole muszą przejść (efekt wykryty / brak fałszywego
alarmu) zanim jakikolwiek kod dotknie klatek UCSD Ped2. Niepowodzenie
którejkolwiek = STOP, raport uczciwy, brak przechodzenia do danych
realnych (dokładnie ten sam gate, co przy `chrono_sphere_bridge`
i innych konstrukcjach GIA-TIMDR w tej sesji).

## 5. Dane referencyjne i testowe (UCSD Ped2)

Źródło: oficjalny UCSD Anomaly Detection Dataset, pobrany przez
`git clone` mirrora `junaidwahid/UCSD-Anomaly-dataset` na GitHubie
(bezpośredni host `svcl.ucsd.edu` zablokowany w tym środowisku przez
allowlist sieciową — `git clone` z github.com nie jest blokowany, ten sam
obejściowy kanał co przy CWRU). Struktura zweryfikowana zgodna z
oryginałem (Train/Test, foldery `_gt`, plik `.m` z zakresami `gt_frame`).

Ze względu na rozmiar (pełny zbiór 1.8GB) do repo trafia TYLKO lekki
podzbiór:
- referencja (zdrowa): pierwsze 4 klipy treningowe Ped2 (`Train001`-`Train004`)
- test: pierwsze 3 klipy testowe Ped2 (`Test001`-`Test003`)

Wybór "pierwsze N" jest CELOWO nie-selektywny (nie przeglądamy klipów
pod kątem tego, które dają ładny wynik) — ustalony PRZED uruchomieniem
testu na realnych danych.

## 6. Plan testu statystycznego

Dla każdego z 3 klipów testowych osobno: podział klatek na grupę
"gt" (`frame ∈ gt_frame` z `UCSDped2.m`) i "non-gt" (reszta). Dla Λ:
Mann-Whitney U (gt vs non-gt) + rozmiar efektu rank-biserial. Dla ρ
(binarne): test Fishera dokładny na tabeli 2×2 (anomalny/nie × gt/nie).
Korekta Bonferroniego dla 3 klipów × 2 testy = 6 porównań,
α_corr = 0.05/6 ≈ 0.0083.

Wynik zgłaszany per klip OSOBNO (nie tylko zbiorczo) — zgodnie z
zastrzeżeniem z RESULT_MODAL_BAND_ENERGY_BRIDGE_v0.2.md o tym, że
zbiorcza istotność nie jest tym samym co specyficzność/spójność między
przypadkami.

## 7. Uczciwe zastrzeżenia z góry

1. Λ i ρ oparte na PROSTEJ różnicy klatka-do-klatki (`Frame.M`), nie na
   optical flow ani żadnym modelu ruchu — to jest świadomie najprostszy
   możliwy sygnał wejściowy, nie próba konkurowania z RAFT/sieciami
   predykcji klatki.
2. Siatka 4×4 i okno τ (w=4) są wyborami startowymi, NIE skalibrowanymi
   na Ped2 — jeśli test przejdzie kontrole syntetyczne, ale da wynik
   niejednoznaczny na realnych danych, następny krok to sprawdzenie
   stabilności względem rozmiaru siatki (analogicznie do sprawdzania
   stabilności okna w `chrono_modal_geometry_bridge`), NIE dostrajanie
   pod already-seen wynik.
3. 3 klipy testowe to mała próba — wynik pozytywny tu jest tropem
   wymagającym replikacji na większym podzbiorze, nie ostatecznym
   dowodem (ta sama zasada co w całym `timdr-signal-framework`).
