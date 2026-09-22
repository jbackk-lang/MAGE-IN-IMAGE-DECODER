# UCSD Anomaly Detection Dataset — Ped2 (podzbiór)

Lekki podzbiór oficjalnego **UCSD Anomaly Detection Dataset** (Ped2),
przygotowany zgodnie z `PREREG_META_DYNAMICS_v0.1.md` (sekcja 5) w
katalogu głównym repo.

## Źródło

Oficjalna strona: http://www.svcl.ucsd.edu/projects/anomaly/dataset.htm
(niedostępna bezpośrednio z tego środowiska — zablokowana przez
allowlist sieciową). Pobrane przez `git clone` mirrora
`https://github.com/junaidwahid/UCSD-Anomaly-dataset` (struktura
zweryfikowana zgodna z oryginałem: Train/Test, foldery `_gt`, plik `.m`
z zakresami `gt_frame`).

## Zawartość tego podzbioru

- `Train/Train001`–`Train004` (600 klatek łącznie) — referencja ZDROWA
  (tylko normalne piesze, bez anomalii — zgodnie z oficjalnym protokołem
  datasetu).
- `Test/Test001`–`Test003` (510 klatek łącznie) — klatki testowe.
- `Test/ground_truth.json` — zakresy klatek anomalnych (`gt_frame`,
  1-indeksowane, WŁĄCZNIE z obiema granicami) wyciągnięte ręcznie z
  oryginalnego `UCSDped2.m` dla TYCH TRZECH klipów.

Klatki skonwertowane z oryginalnego formatu TIFF (PackBits) do PNG
(bezstratnie, ta sama rozdzielczość 240×360, `cv2.IMWRITE_PNG_COMPRESSION=9`)
wyłącznie żeby zmniejszyć rozmiar w repo (~46MB zamiast ~85MB) — wartości
pikseli niezmienione.

Wybór "pierwsze 4 treningowe / pierwsze 3 testowe" jest ZAMROŻONY w
PREREG PRZED uruchomieniem jakiegokolwiek testu na tych danych — nie jest
to selekcja klipów, które dają ładny wynik.

## Cytowanie (oryginalny dataset)

> Anomaly Detection in Crowded Scenes.
> V. Mahadevan, W. Li, V. Bhalodia and N. Vasconcelos.
> In Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR),
> San Francisco, CA, 2010.
