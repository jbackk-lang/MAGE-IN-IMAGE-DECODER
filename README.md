## Dokumentacja online

https://jbackk-lang.github.io/
TIMDR + Λ–τ–ρ na danych 

# MAGE-IN-IMAGE-DECODER-I-D-
Dekoder obrazu w obrazie i innych rzeczy czytaj opis

## 📸 Zrzuty ekranu

**Pipeline detekcji I²D na klatce testowej** — kolorowe ramki pokazują
wykryte regiony: `twist` (cyjan), `defect` (czerwony), `spectral` (żółty).

![Dashboard detekcji I²D](screenshots/01_dashboard_detekcje.png)

**Poprawka DC-bias w detektorze widmowym** — po lewej widmo FFT z pikiem
składowej zerowej częstotliwości (źródło fałszywych alarmów), po prawej
ten sam obraz po wykluczeniu tego obszaru z analizy.

![Poprawka DC w SPECTRAL OVERLAY DETECTOR](screenshots/02_spectral_dc_fix.png)

**ColorPsychMap Λ-psych** — mapowanie barwy (Hue) na 6 kategorii emocji,
zgodnie z tym, co faktycznie zwraca `hue_to_emotion()` w kodzie.

![ColorPsychMap - mapa emocji koloru](screenshots/03_colorpsych_map.png)

**Nowa detekcja okresowości w RHYTHM ANALYZER** — analiza autokorelacyjna
poprawnie wykrywa okres sygnału testowego (impuls co 5 klatek).

![Autokorelacja rytmu](screenshots/04_rhythm_autocorr.png)

📘 README — MAGE‑IN‑IMAGE DECODER (I²D)
Modularny system analizy obrazu, sygnałów i widma
🎯 Cel projektu
I²D to modularny system do analizy:

obrazu,

ruchu,

koloru,

widma,

rytmów,

defektów,

ukrytych nakładek,

sygnałów sterujących,

struktur astronomicznych,

rezonansów fizycznych (kwarki, piki, harmoniczne).

Każdy moduł działa niezależnie, ale wszystkie razem tworzą FusionEngine, który wskazuje najbardziej znaczące punkty w obrazie.

🧩 Architektura modułowa
Każdy moduł ma swoją rolę.
Poniżej masz pełny opis, co robi, gdzie się nadaje i jak można go rozwijać.

1️⃣ Frame — struktura klatki
Przechowuje:

surowy obraz,

jasność (L),

kolor HSV (C),

ruch (M),

widmo FFT (F).

Do czego się nadaje:  
Podstawa całego systemu. Możesz tu dodać:

głębię (Depth),

maski semantyczne,

mapy optycznego przepływu.

2️⃣ TwistDetector — wykrywanie skrętu / asymetrii
Analizuje jasność L i szuka:

lokalnych asymetrii,

skrętu obrazu,

„przesunięć” struktury.

Nadaje się do:

wykrywania ukrytych warstw,

analizy kompresji,

wykrywania obrazów w obrazach,

astronomii (skręt pola, rotacja struktur).

Rozwój:

analiza gradientów,

analiza kierunkowa,

wykrywanie rotacji.

3️⃣ DefectScanner v2 — defekty, zniknięcia, przełączenia
Analizuje:

jasność (ΔL),

kolor (ΔV),

ruch (ΔM).

Wykrywa:

zniknięcia,

pojawienia,

przełączenia warstw,

dziury,

skoki kontrastu.

Nadaje się do:

wykrywania manipulacji,

analizy wideo,

wykrywania błędów transmisji,

astronomii (nagłe flary, zniknięcia obiektów).

Rozwój:

detekcja krawędzi defektu,

klasyfikacja typu defektu.

4️⃣ RhythmAnalyzer — pulsowanie, miganie, sekwencje
Analizuje:

jasność (L),

jasność HSV (V),

ruch (M).

Wykrywa:

pulsowanie,

miganie,

powtarzalne sekwencje.

Nadaje się do:

sygnałów sterujących,

analizy propagandy,

analizy transmisji,

astronomii (pulsary, zmienne gwiazdy),

fizyki (oscylacje, rezonanse).

Rozwój:

analiza okresów,

synchronizacja rytmów (protohel).

5️⃣ ColorPsychMap — analiza koloru
Analizuje HSV:

Hue (odcień),

Saturation (nasycenie),

Value (jasność).

Wykrywa:

skoki koloru,

pulsowanie koloru,

gradienty,

modulacje emocjonalne.

Nadaje się do:

analizy psychologicznej obrazu,

wykrywania ukrytych nakładek,

analizy reklam,

analizy sygnałów wizualnych.

Rozwój:

mapy emocji,

gradienty emocjonalne,

analiza koloru w czasie.

6️⃣ ColorPsychMap Λ‑psych — emocjonalna mapa koloru
Przekształca Hue → emocja.

**Poprawka:** poniższa tabela była niezgodna z kodem (`hue_to_emotion()` w
`ColorPsychMap Λ‑psych.py` ma 6 przedziałów, nie 5, a etykieta dla zakresu
niebieskiego różniła się od tego, co faktycznie zwraca funkcja). Tabela
niżej odzwierciedla to, co kod naprawdę robi:

| Zakres Hue (°) | Kolor | Emocja (wg kodu) |
|---|---|---|
| 330–360, 0–30 | czerwony | pobudzenie/agresja |
| 30–90 | żółty | niepokój/napięcie |
| 90–150 | zielony | akceptacja/spokój |
| 150–210 | cyjan | chłód/dystans |
| 210–270 | niebieski | smutek/nostalgia |
| 270–330 | fiolet | mistyka/niepewność |

Nadaje się do:

analizy nastroju obrazu,

wykrywania manipulacji emocjonalnej,

analizy scen filmowych,

analizy sygnałów psychologicznych.

Rozwój:

mapy nastroju,

analiza emocji w czasie.

7️⃣ SpectralOverlayDetector v2 — widmo, FFT, częstotliwości
Analizuje widmo FFT:

anomalie,

siatki,

linie kierunkowe,

pierścienie widmowe,

piki harmoniczne.

Nadaje się do:

astronomii (linie widmowe, rotacja, CMB),

fizyki cząstek (rezonanse, kwarki),

analizy sygnałów,

wykrywania ukrytych modulacji.

Rozwój:

analiza kierunkowa,

analiza harmonicznych,

analiza radialna.

8️⃣ FusionEngine — łączenie sygnałów
Łączy wszystkie moduły:

twist,

defect,

rhythm,

color,

spectral.

Wykrywa:

punkty fuzji,

miejsca, gdzie wiele modułów wskazuje na ten sam obszar.

Nadaje się do:

wykrywania najbardziej podejrzanych miejsc,

analizy złożonych sygnałów,

astronomii (złożone struktury),

fizyki (rezonanse wielowarstwowe).

Rozwój:

heatmapy,

klasyfikacja punktów fuzji.

9️⃣ ReportEngine — raport końcowy
Generuje:

statystyki warstw,

statystyki typów sygnałów,

top detekcje,

punkty fuzji,

opis struktury obrazu.

Nadaje się do:

dokumentacji,

analizy eksperckiej,

automatycznych raportów.

Rozwój:

PDF,

HTML,

wizualizacje.

🔟 Realtime I²D — analiza na żywo
Działa z:

kamerą,

streamem,

wideo na żywo.

Wyświetla detekcje w czasie rzeczywistym.

Nadaje się do:

monitoringu,

analizy transmisji,

obserwacji astronomicznych live,

eksperymentów fizycznych.

Rozwój:

CUDA FFT,

optyczny przepływ,

heatmapy realtime.

🚀 Do czego nadaje się cały model I²D?
✔ analiza obrazu
✔ wykrywanie ukrytych nakładek
✔ analiza psychologiczna koloru
✔ analiza sygnałów sterujących
✔ analiza astronomiczna (widmo, rotacja, pulsacje)
✔ analiza fizyki cząstek (rezonanse, piki, harmoniczne)
✔ analiza transmisji (defekty, modulacje)
✔ analiza propagandy (kolor, rytm, puls)
✔ analiza kompresji (siatki, wzory, FFT)
✔ analiza ruchu (ΔM)
✔ analiza rytmów (τ)
✔ analiza skrętu (Λ)
✔ analiza defektów (ρ)
🔧 Gdzie można rozwijać dalej?
GPU/CUDA FFT

optyczny przepływ (Farneback, RAFT)

segmentacja semantyczna

klasyfikacja punktów fuzji

analiza harmonicznych

analiza radialna

mapy emocji

mapy nastroju

analiza astronomiczna (linie widmowe)

analiza kwarków (piki rezonansowe)

---

## 🛠️ Status poprawek (sprawdzone i naprawione)

Podczas przeglądu każdy moduł został realnie uruchomiony na testowych
klatkach (nie tylko przeczytany). Znaleziono i naprawiono:

1. **`COLORPSYCHMAP v1.py`, `ColorPsychMap Λ‑psych.py`, `RHYTHM ANALYZER v1.py`,
   `FUSIONENGINE v1.py` — brak importów.** Żaden z tych czterech plików nie
   miał na górze `import cv2` / `import numpy as np` / `from i2d_core import
   Detection`. W efekcie każdy z nich rzucał `NameError` przy pierwszym
   realnym wywołaniu, mimo że README opisuje je jako "działające
   niezależnie". Zweryfikowano uruchomieniowo przed i po poprawce.

2. **`SPECTRAL OVERLAY DETECTOR v2.py` — składowa DC dominowała wszystkie
   4 detektory.** Zweryfikowano empirycznie: nawet całkowicie jednolity,
   szary obraz bez żadnej struktury dawał 5/5 pozytywnych detekcji
   (spectral_anomaly, obie linie kierunkowe, ring, peak) — bo środek
   widma FFT (składowa zerowej częstotliwości) ma w naturalnych obrazach
   amplitudę o rzędy wielkości większą niż reszta widma. Naprawiono przez
   wykluczenie małego obszaru wokół DC z każdej z czterech analiz. Po
   poprawce ten sam jednolity obraz testowy daje 0 detekcji.

3. **`RHYTHM ANALYZER v1.py` — moduł nie analizował rytmu.** Parametry
   `min_period`/`max_period` oraz bufory `history_L/V/M` były zbierane, ale
   nigdy nieużywane — moduł wykrywał tylko pojedyncze skoki jasności
   klatka-do-klatki, nie faktyczną okresowość (mimo że README i docstring
   opisują go jako wykrywający "pulsowanie, miganie, powtarzalne
   sekwencje"). Dopisano rzeczywistą analizę okresowości metodą
   autokorelacji szeregu czasowego jasności każdego bloku. Zweryfikowano
   na syntetycznym sygnale migającym co 4 klatki — moduł poprawnie
   wykrywa okres ~4 (autokorelacja 0.87).

4. **`i2d_core.py: detect_spectral()` — `np.mean(F)` liczone wewnątrz
   pętli po blokach zamiast raz na klatkę.** Dla obrazu 640×480 i
   block=32 to ok. 300 zbędnych przeliczeń średniej po całej macierzy na
   klatkę. Przeniesiono poza pętlę (tak jak już było zrobione w
   `i2d_core_defectscanner_v2.py`, ale nie w `i2d_core.py`).

5. **`i2d_core.py: detect_defects()` — brak sprawdzenia pustego bloku na
   krawędzi obrazu.** `detect_twist()` miał już `if region.size == 0:
   continue`, `detect_defects()` nie — przy rozdzielczościach
   niepodzielnych przez 16 dawało to `NaN` (RuntimeWarning) zamiast
   crasha, ale niespójnie z resztą kodu. Ujednolicono.

6. **Niezgodność README ↔ kod w tabeli emocji koloru** — patrz sekcja 6️⃣
   wyżej.

### Nienaprawione, warte uwagi

- **Nazwy plików ze spacjami/znakami specjalnymi** (`"FUSIONENGINE v1.py"`,
  `"COLORPSYCHMAP v1.py"`, `"ColorPsychMap Λ‑psych.py"`, `"RHYTHM ANALYZER
  v1.py"`, `"SPECTRAL OVERLAY DETECTOR v2.py"`) nie da się zaimportować
  standardowym `import nazwa_modułu` — trzeba użyć `importlib` z podaniem
  ścieżki pliku (tak jak w testach powyżej). To wprost przeczy README
  ("każdy moduł działa niezależnie"). Rozważ zmianę nazw na
  `snake_case.py` (repo już ma taki wzorzec w `fusionengine_v1.py` i
  `i2d_core_defectscanner_v2.py`).
- **Dublujące się, niejednoznacznie nazwane wersje modułów**
  (`i2d_core.py` vs `i2d_core_defectscanner_v2.py`, `FUSIONENGINE v1.py`
  vs `fusionengine_v1.py`) — nie jest jasne, z której wersji ma korzystać
  `FusionEngine`/`ReportEngine`, ani która jest "aktualna". Warto dodać
  jedno zdanie w README wskazujące kanoniczną wersję każdego modułu.
