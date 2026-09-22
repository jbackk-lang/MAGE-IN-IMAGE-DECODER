# RESULT — CONTOUR_CURVATURE v0.1 (G-branch, krzywizna konturów 2D)

Status: bramka syntetyczna PRZESZŁA, test główny na realnych danych
wykonany zgodnie z `PREREG_CONTOUR_CURVATURE_v0.1.md` +
`PREREG_CONTOUR_CURVATURE_v0.1_ADDENDUM.md`. Wynik zgłoszony w całości, bez
donastrajania po zobaczeniu wyniku.

## 0. Poprawka metodologiczna znaleziona PRZED bramką (odnotowana uczciwie)

Pierwsza wersja kontroli syntetycznych porównywała Mann-Whitney U na
surowych, pojedynczych wartościach krzywizny punkt-po-punkcie między
dwoma regionami. To dawało stopę fałszywych alarmów 15-40% (zamiast
oczekiwanych ~5%) na czystej kontroli negatywnej — złamanie założenia
niezależności obserwacji MWU, bo punkty wzdłuż tego samego konturu są
silnie skorelowane (dokładnie ten błąd, przed którym ostrzega
`timdr-signal-framework` §2: operator okna wymaga rozłącznych,
niezależnych obserwacji). Poprawka: jednostką porównania jest JEDNA
podsumowująca wartość `G_kappa` (gęstość szczytów krzywizny) PER REGION
PER OBRAZ/ŁATKA, nie punkt konturu. Po poprawce obie kontrole przechodzą
czysto (patrz sekcja 1). To poprawka metody PRZED zobaczeniem jakichkolwiek
danych realnych — dozwolona przez protokół prerejestracji (dostrajanie
zabronione PO, nie w trakcie budowy samej bramki).

Druga korekta: syntetyczne obrazy "naturalne" zbudowano z losowych okręgów
(gładka krzywizna 1/promień) zamiast rozmytego szumu Gaussa — czysty szum
Gaussa albo nie dawał żadnych wykrywalnych konturów (zbyt rozmyty), albo
przy niższym rozmyciu dawał artefakty schodkowe siatki pikseli
dominujące nad prawdziwą krzywizną geometryczną (zbyt czuły Canny na
szum). Odnotowane jako uczciwe ograniczenie metody: dyskretna krzywizna
konturu z `cv2.findContours` jest wrażliwa na parametry Canny i wymaga
kontrastowych, w miarę czystych krawędzi, żeby uniknąć artefaktów
pikselowych.

## 1. Bramka syntetyczna (`test_contour_curvature.py`) — 7/7 PASSED

- Testy jednostkowe wzoru krzywizny (linia prosta ≈0, narożniki kwadratu
  dają wyraźne szczyty): PASSED.
- **Kontrola pozytywna**: gęstość szczytów krzywizny w regionie wklejonego
  ostrego prostokąta istotnie wyższa niż w regionie odległym (Mann-Whitney,
  n=60 obrazów/grupa, p<0.05, kierunek zgodny z hipotezą). PASSED.
- **Kontrola negatywna**: dwa regiony tego samego typu naturalnej tekstury
  (bez wklejenia) nie dają istotnej różnicy (p≥0.05, n=60/grupa). PASSED.

## 2. Dane realne — CASIA v2 groundtruth (N=4, jawne ograniczenie mocy)

| Obraz | Typ | n_boundary | n_bg | mean_boundary | mean_bg | p | istotne (α=0.0125) |
|---|---|---|---|---|---|---|---|
| Tp_D_CRN_M_N_pla00035_pla00033_10997 | splicing | 37 | 16 | 0.1031 | 0.1006 | 0.304 | NIE |
| Tp_D_CRN_S_N_nat00033_cha00086_11502 | splicing | 38 | 26 | 0.0210 | 0.0283 | 0.9996 | NIE (kierunek przeciwny) |
| Tp_S_NNN_S_O_pla00077_pla00077_11212 | copy-move | 39 | 25 | 0.0376 | 0.0371 | 0.560 | NIE |
| Tp_S_NRN_S_N_pla00005_pla00005_10937 | copy-move | 30 | 29 | 0.0537 | 0.0434 | **0.0014** | **TAK** |

Korekta Bonferroniego: `α_corr = 0.05/4 = 0.0125`.

**1 z 4 obrazów istotny** (Tp_S_NRN_S_N — copy-move), kierunek zgodny z
hipotezą (boundary>tło). Pozostałe 3 nieistotne; jeden z dwóch obrazów
splicing (Tp_D_CRN_S_N) miał kierunek PRZECIWNY (boundary<tło, choć
p≈1, więc to nie jest istotny efekt w złym kierunku, tylko brak sygnału).

## 3. Decyzja (reguła zamrożona w ADDENDUM sekcja "Reguła decyzji")

**CZĘŚCIOWO SUPPORTED** (istotne na 1 z 4, kierunek zgodny z hipotezą na
tym jednym obrazie — próg dla SUPPORTED to ≥3 z 4, nieosiągnięty).

## 4. Interpretacja i uczciwe ograniczenia

- **N=4 to bardzo mała próba** — oryginalny zbiór CASIA v2 (Au/Tp ~12000
  obrazów) nie jest już publicznie hostowany (link tylko przez ręczną
  zgodę na Google Drive); jedyne bezpośrednio dostępne, realne dane z
  ground truth to 4 przykłady w mirror `namtpham/casia2groundtruth`. Ta
  próba NIE ma mocy do wykrycia efektu średniej wielkości z jakąkolwiek
  pewnością — wynik jest wstępnym tropem, nie ustaloną odpowiedzią
  (patrz `timdr-signal-framework` §2 punkt 9: pojedynczy pozorny sygnał
  wymaga replikacji na niezależnym zbiorze przed uznaniem za ustalony).
- **Próg referencyjny liczony wewnątrz-obrazowo** (z łatek tła tego
  samego obrazu, nie z osobnego zbioru autentycznych obrazów) — odchylenie
  od PREREG v0.1 §1, jawnie odnotowane w ADDENDUM PRZED testem głównym.
  To słabszy standard niż "zdrowa referencja" używana w innych gałęziach
  TIMDR (np. `bearing_meta_adapter`, `meta_dynamics_v1`) i mogło zaniżyć
  czułość testu (próg kalibrowany na tym samym obrazie, który testujemy).
- **Rozróżnienie splicing vs copy-move**: jedyny istotny wynik pochodzi z
  obrazu copy-move, nie splicing — to nieco zaskakujące względem hipotezy
  z PREREG (spodziewano się, że wklejenie z INNEGO źródła (splicing) da
  ostrzejsze, bardziej "obce" granice niż kopiowanie w obrębie tego samego
  obrazu). Zbyt mała próba (2 obrazy na typ), żeby wyciągnąć wniosek o
  różnicy między typami manipulacji.
- Zgodnie z regułą z PREREG v0.1 §5: to NIE jest CZYSTE "NOT SUPPORTED",
  więc gałąź nie jest jeszcze zamknięta, ale też nie jest wystarczająco
  mocna, żeby uznać hipotezę za potwierdzoną. Dalsza praca (jeśli w ogóle)
  wymagałaby większego, niezależnego zbioru z prawdziwą referencją
  autentycznych obrazów — nie retuningu tej samej metody na tych samych
  4 obrazach.

**Ocena całościowa gałęzi CONTOUR_CURVATURE (G-branch, v0.1): CZĘŚCIOWO
SUPPORTED, niska moc (N=4), wymaga replikacji na większym zbiorze przed
jakąkolwiek dalszą interpretacją.**
