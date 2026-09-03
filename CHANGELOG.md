# Changelog / notatki techniczne

Zapis realnych błędów znalezionych i naprawionych podczas przeglądu kodu —
każdy moduł został uruchomiony na testowych klatkach, nie tylko przeczytany.
Szczegóły implementacyjne i uzasadnienia patrz `tests/test_i2d_core.py` oraz
komentarze `POPRAWKA` w kodzie.

## Naprawione

1. **Brak importów** w `COLORPSYCHMAP v1.py`, `ColorPsychMap Λ‑psych.py`,
   `RHYTHM ANALYZER v1.py`, `FUSIONENGINE v1.py` — każdy rzucał `NameError`
   przy pierwszym realnym wywołaniu, mimo README opisującego je jako
   "działające niezależnie".
2. **DC-bias w detekcji widmowej** — składowa zerowej częstotliwości FFT
   dominowała widmo w naturalnych obrazach, dając fałszywe alarmy niemal
   na każdej klatce (jednolity szary obraz: 5/5 fałszywych detekcji).
   Wykluczono mały obszar wokół DC z każdej z czterech analiz.
3. **RhythmAnalyzer w ogóle nie liczył okresowości** — `min_period`/
   `max_period` i bufory `history_L/V/M` były zbierane, ale nieużywane;
   moduł łapał tylko pojedyncze skoki klatka-do-klatki. Dodano
   autokorelację (zweryfikowano na sygnale co 4 klatki → wykryty okres
   ~4, korelacja 0.87).
4. **Wydajność `detect_spectral()`** — `np.mean(F)` liczone w pętli po
   blokach zamiast raz na klatkę (~300× zbędnych przeliczeń przy 640×480,
   block=32).
5. **Brak guardu na pusty blok** w `detect_defects()` — rozdzielczości
   niepodzielne przez `block_size` dawały `NaN` zamiast czystego pominięcia
   (niespójnie z `detect_twist()`, który już to miał).
6. **Tabela emocji koloru w README nie zgadzała się z kodem** —
   `hue_to_emotion()` ma 6 przedziałów, nie 5, inna etykieta dla niebieskiego.
7. **DC-bias naprawiony tylko w 1 z 3 niezależnych kopii tej samej
   detekcji widmowej** — `i2d_core.py::detect_spectral()` i
   `i2d_core_defectscanner_v2.py::detect_spectral()` nadal dawały
   fałszywe `spectral_anomaly`. `detect_spectral()` deleguje teraz do
   jedynej implementacji w `spectral_overlay_detector_v2.py`.
8. **`run_i2d()` łączył tylko 3 z 5 modułów obiecanych przez FusionEngine**
   — `detect_rhythm` i `detect_color_emotion` nigdy nie trafiały do listy
   detekcji. Pipeline woła teraz wszystkich pięć (regresja:
   `test_run_i2d_image_mode_includes_color_module`).
9. **Dwie różne wersje progu w `detect_defects()`** (sztywny 25 vs
   adaptacyjny `mean(M)+2*std(M)`, min. 10.0) — ujednolicono na
   adaptacyjny.
10. **Okresowość liczona wcześniej tylko dla jasności (L)**, nie dla V/M
    mimo zbieranych buforów — dodano `rhythm_periodic_color` i
    `rhythm_periodic_motion`.
11. **Zduplikowane moduły → jedna kanoniczna wersja + cienki re-eksport.**
    Każdy moduł ma teraz jeden plik snake_case niosący logikę
    (`i2d_core.py`, `fusionengine_v1.py`, `reportengine_v1.py`,
    `rhythm_analyzer_v1.py`, `colorpsychmap_v1.py`,
    `colorpsychmap_lambda_psych.py`, `spectral_overlay_detector_v2.py`).
    Stare pliki (nazwy ze spacjami, `i2d_core_defectscanner_v2.py`,
    `FUSIONENGINE v1.py`) zostały jako trwałe aliasy — usuwanie
    wymagałoby przepisania linków w README i na stronie dokumentacji —
    ale są teraz jednolinijkowymi re-eksportami pilnowanymi testami
    asercji **tożsamości obiektu** (`is`, nie tylko równy wynik), żeby
    nikt nie wkleił z powrotem niezależnej kopii.
12. **Brak `requirements.txt` i testów w repo** mimo że README opisywało
    realne uruchomienia weryfikacyjne. Dodano `requirements.txt`
    (opencv-python, numpy) i `tests/test_i2d_core.py` (pytest, 22 testy)
    pokrywający punkty 7–11 wyżej plus pozytywną/negatywną kontrolę dla
    DC-bias.

## Nienaprawione / warte uwagi

- Import `detect_rhythm`/`detect_color_emotion` w `run_i2d()` jest celowo
  lokalny (wewnątrz funkcji), żeby uniknąć cyklicznego importu z
  `i2d_core` — zrewidować, jeśli te moduły zaczną importować z `i2d_core`
  coś więcej niż samą klasę `Detection`.
- Realtime I²D i moduł GPU/CUDA są na razie tylko opisem w README — nie
  ma jeszcze odpowiadającego im pliku w repo.
