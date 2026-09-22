# PREREG — CONTOUR_CURVATURE v0.1 (G-branch, krzywizna konturów 2D)

Status: ZAMROŻONE PRZED dotknięciem jakichkolwiek danych realnych (obrazów z
ground truth). Zmian po zobaczeniu wyniku na danych realnych NIE robimy —
złamałoby to protokół prerejestracji (patrz `timdr-signal-framework` §2).

## 0. Kontekst i odróżnienie od istniejącego kodu

Sprawdzone PRZED napisaniem tego dokumentu (patrz research w tej sesji):

- `TIMDR-Geometry-Formalism/timdr_geometry/weingarten.py` implementuje
  operator kształtu (Weingarten) dla **siatek trójkątów 3D** (Axiomy G8-G9) —
  normalne wierzchołkowe, sąsiedztwo 1-ring, rzut na płaszczyznę styczną.
  To NIE jest matematyka dla krzywej 2D (kontur obrazu nie ma płaszczyzny
  stycznej ani operatora kształtu w tym sensie) — nie da się tego odtworzyć
  ani zaadaptować, tylko wymaga osobnego, dużo prostszego wzoru na krzywiznę
  krzywej płaskiej.
- `MAGE-IN-IMAGE-DECODER::i2d_core.py::detect_twist()` ("TwistDetector",
  "lokalna asymetria / skręt") liczy coś zupełnie innego: różnicę średnich
  jasności między lewą/prawą i górą/dołem bloku pikseli. Nie ma pojęcia
  konturu, gradientu ani krzywizny — brak kolizji nazw/zakresu.
- W repo nie ma żadnego istniejącego kodu do `cv2.findContours`/`Canny`/
  krzywizny (grep pusty).

Nowy moduł: `contour_curvature.py` (ten repo, bo już ma zależność
`opencv-python` i istniejący pipeline obrazowy `i2d_core`).

## 1. Definicja obiektu i metryki (ZAMROŻONE)

**Ekstrakcja konturu**: `cv2.Canny(gray, low, high)` → `cv2.findContours(...,
cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)` (bez aproksymacji — potrzebujemy
gęstych punktów konturu do liczenia krzywizny). Kontury krótsze niż
`MIN_CONTOUR_LEN=20` punktów odrzucane (za mało punktów na stabilną
krzywiznę).

**Dyskretna krzywizna wzdłuż konturu** (klasyczny wzór na krzywiznę
dyskretną krzywej, kąt zmiany kierunku na jednostkę długości łuku, NIE
wzór Weingartena z gałęzi 3D):

Dla punktu `p_i` z sąsiadami `p_{i-k}`, `p_{i+k}` (krok `k=CURVATURE_STEP=3`
punktów konturu, żeby stłumić szum kwantyzacji pikseli):
```
v1 = p_i - p_{i-k}
v2 = p_{i+k} - p_i
dtheta = kąt(v1, v2)  # atan2 różnicy kierunków, w (-pi, pi]
ds = (|v1| + |v2|) / 2
kappa_i = |dtheta| / ds
```
Kontury zamknięte (pętla `i` modulo długość konturu); otwarte fragmenty na
brzegu obrazu pomijane (brak `p_{i-k}`/`p_{i+k}`).

**Metryka per obraz/region**: `G_kappa = gęstość szczytów krzywizny` =
udział punktów konturu z `kappa_i > kappa_thresh` wśród wszystkich punktów
konturu w regionie, gdzie `kappa_thresh` = próg MAD wyznaczony z obrazów
REFERENCYJNYCH (zdrowych/nienaruszonych), analogicznie do konwencji
`mediana+k·MAD` używanej w całym ekosystemie TIMDR. `K_ROBUST=3.0`
(wartość startowa, NIE kalibrowana na direct — patrz sekcja 5, jeśli
kalibracja będzie potrzebna, będzie to OSOBNA, jawnie prerejestrowana
runda, jak w `META_DYNAMICS_RHO_CALIBRATION`).

**Hipoteza testowana**: regiony obrazu z wklejoną/zmanipulowaną treścią
(splicing) mają WYŻSZĄ gęstość szczytów krzywizny na granicy wklejenia niż
regiony naturalne — bo cięcie+wklejenie zwykle wprowadza nienaturalnie
ostre narożniki/nieciągłości krzywizny, których granice obiektów naturalnych
(cienie, fałdy, liście, twarze) zwykle nie mają w tym samym natężeniu.

## 2. Model null i porównanie

Test dwupróbkowy: `G_kappa` (gęstość szczytów krzywizny) w oknie/regionie
"ground truth forged" vs. region "non-forged" na TYCH SAMYCH obrazach
(nie różne obrazy — kontrola za oświetleniem/kompresją/treścią sceny).
Mann-Whitney U + rank-biserial effect size (konwencja z §2
`timdr-signal-framework`).

## 3. Kontrole syntetyczne (WYMAGANE, muszą przejść PRZED danymi realnymi)

**Pozytywna**: naturalny szum Perlina/gładki gradient (symulacja "naturalnej"
tekstury, brak ostrych krawędzi) + wklejony OSTRY prostokąt/wielokąt
(symulacja splicingu — ostre narożniki 90°). `G_kappa` w regionie wklejenia
musi być istotnie wyższe niż poza nim.

**Negatywna**: sam naturalny szum/gradient BEZ wklejenia, porównanie dwóch
losowych regionów tego samego obrazu — brak istotnej różnicy `G_kappa`
(false-positive rate pod kontrolą, próg jak w poprzednich gałęziach: cel
`<0.15` false-positive na powtórzeniach z różnymi seedami).

Obie kontrole w `test_contour_curvature.py`, uruchamiane PRZED jakimkolwiek
dotknięciem prawdziwego zbioru forgery.

## 4. Dane realne (plan)

Zbiór z ground-truth maskami splicingu/kopiuj-wklej (kandydaci do
wyszukania: CASIA v2, Columbia Uncompressed Splicing, COVERAGE — wybór
zależny od dostępności przez `git clone` z GitHub, analogicznie do obejścia
UCSD Ped2 w tej samej sesji). Test główny na podzbiorze z jawną maską
(region forged vs non-forged per obraz), liczba porównań i korekta
Bonferroniego ustalona PO znalezieniu konkretnego zbioru (wpisane do
addendum PRZED odpaleniem testu głównego, nie po).

## 5. Reguła decyzji (zamrożona)

- **SUPPORTED**: istotny (po korekcie Bonferroniego) efekt w kierunku
  forged>non-forged na większości testowanych obrazów/porównań.
- **CZĘŚCIOWO SUPPORTED**: istotny efekt na części, ale nie większości.
- **NOT SUPPORTED**: brak istotnego efektu, lub efekt w kierunku
  przeciwnym.

Jeśli kontrola syntetyczna (sekcja 3) nie przejdzie — STOP przed dotknięciem
danych realnych, dokładnie jak w `META_DYNAMICS_v0.2` (dokumentujemy
zatrzymanie, nie naciągamy progu).
