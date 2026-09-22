# ADDENDUM — dane realne (PREREG_CONTOUR_CURVATURE_v0.1.md sekcja 4)

ZAMROŻONE PRZED uruchomieniem testu głównego, po znalezieniu konkretnego
zbioru danych.

## Zbiór danych

`namtpham/casia2groundtruth` (GitHub, mirror grunt prawdy CASIA v2 —
oryginalny host niedostępny, autor repo jawnie to opisuje). Oryginalne
obrazy tamperowane CASIA v2 nie są już hostowane publicznie (link do
Google Drive w README wymaga ręcznej zgody) — jedyne bezpośrednio
dostępne, realne pary obraz+maska to katalog `Samples/` tego repo:
**4 obrazy** z maskami ground-truth (binarne, 0/255):
- 2 splicing ("Tp_D_..." — inne źródło, "D"=different)
- 2 copy-move ("Tp_S_..." — to samo źródło, "S"=same)

Jawne ograniczenie: N=4 to bardzo mała próba, moc statystyczna niska.
Zgłaszamy wynik uczciwie niezależnie od tego (patrz `timdr-signal-framework`
§2 punkt 8 — sprawdzenie mocy PRZED odczytaniem wysokiego p jako
potwierdzenia braku efektu). Brak osobnego zbioru obrazów AUTENTYCZNYCH
(nietamperowanych) w tym mirror — próg referencyjny liczony
WEWNĄTRZ-obrazowo z łatek dalekich od maski (patrz niżej), nie z osobnego
zbioru "zdrowego". To odchylenie od PREREG v0.1 sekcji 1 (tam założono
próg z osobnych obrazów referencyjnych) — jawnie odnotowane, nie ukryte.

## Metoda (per obraz)

1. Wczytaj obraz w skali szarości + maskę binarną.
2. Wyznacz kontur obszaru maski (`cv2.findContours` na masce) — to granica
   wklejenia/kopiowania.
3. Wylosuj `N_BOUNDARY=40` łatek `PATCH=48×48 px` wyśrodkowanych na
   losowych punktach konturu maski (z marginesem, żeby granica mieściła
   się w łatce), oraz `N_BG=40` łatek tego samego rozmiaru z lokalizacji
   ODLEGŁYCH od maski (środek łatki minimum `MIN_DIST=60px` od najbliższego
   punktu maski), losowane bez powtórzeń w miarę możliwości.
4. Próg krzywizny: `compute_reference_threshold` na WSZYSTKICH łatkach
   tła (`N_BG`) tego obrazu (self-referential, patrz ograniczenie wyżej).
5. `region_kappa_density` per łatka (i boundary, i tło) względem tego
   progu.
6. Mann-Whitney U (jednostronny, boundary>tło) na wektorach gęstości
   boundary vs tło, per obraz — 4 testy, korekta Bonferroniego
   `α_corr=0.05/4=0.0125`.

## Reguła decyzji (niezmieniona z PREREG v0.1 sekcji 5, doprecyzowana dla N=4)

- **SUPPORTED**: istotne (po Bonferronim) na ≥3 z 4 obrazów, kierunek
  boundary>tło.
- **CZĘŚCIOWO SUPPORTED**: istotne na 1-2 z 4, kierunek boundary>tło.
- **NOT SUPPORTED**: brak istotności na żadnym, lub kierunek przeciwny.

Wynik dla splicing (Tp_D_, 2 obrazy) i copy-move (Tp_S_, 2 obrazy)
raportowany OSOBNO opisowo (różne mechanizmy manipulacji, różne
oczekiwania co do ostrości granicy) — decyzja SUPPORTED/NOT dotyczy
całości N=4, ale interpretacja rozróżnia oba typy.
