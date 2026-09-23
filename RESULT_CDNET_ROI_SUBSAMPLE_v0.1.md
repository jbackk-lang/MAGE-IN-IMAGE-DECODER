# CDnet: ROI/LK i przepływ co drugą klatkę — pomiar eksploracyjny

Po teście MOG2 + pola wektorowego dodano dwa warianty oszczędzania czasu:

- `mog2_sparse_lk`: MOG2 wskazuje ROI; punkty Shi–Tomasi wybierane są
  tylko w tym obszarze, piramidalny Lucas–Kanade śledzi je między
  klatkami, a wektory są agregowane w bloki 16×16.
- `mog2_cached_flow_2`: Farnebäck na połowie rozdzielczości jest
  aktualizowany co drugą klatkę, przemieszczenie dzielone przez liczbę
  klatek między aktualizacjami, a pomiędzy nimi ostatnia maska
  wektorowa jest ponownie używana razem z **bieżącą** maską MOG2.

Warianty powstały **po obejrzeniu wcześniejszych wyników** na tych
sekwencjach, więc poniższy pomiar jest eksploracyjny, nie niezależnym
potwierdzeniem. Progi i kod nie były zmieniane po wyniku tego przebiegu.

| Sekwencja | Metoda | Precision | Recall | F1 | Średni czas/klatkę |
| --- | --- | ---: | ---: | ---: | ---: |
| highway (1231 klatek ocenianych) | MOG2 | 0.7133 | **0.9109** | 0.8001 | **3.5 ms** |
| highway | MOG2 ∩ pełne pole wektorów | 0.9050 | 0.7301 | **0.8082** | 15.6 ms |
| highway | MOG2 ∩ rzadki LK w ROI | **0.9820** | 0.3866 | 0.5548 | 7.1 ms |
| highway | MOG2 ∩ pole co 2 klatki | 0.8997 | 0.7263 | 0.8038 | 9.8 ms |
| canoe (390 klatek ocenianych) | MOG2 | 0.3456 | **0.8038** | 0.4834 | **4.4 ms** |
| canoe | MOG2 ∩ pełne pole wektorów | 0.4062 | 0.7998 | 0.5388 | 17.2 ms |
| canoe | MOG2 ∩ rzadki LK w ROI | 0.2985 | 0.3783 | 0.3337 | 10.2 ms |
| canoe | MOG2 ∩ pole co 2 klatki | **0.4089** | 0.8007 | **0.5413** | 11.0 ms |

Makro F1: MOG2 `0.6417`; pełna fuzja `0.6735`; LK/ROI `0.4442`;
przepływ co 2 klatki `0.6726`. W tym przebiegu wariant co drugą
klatkę jest ok. **1.6× szybszy od pełnej fuzji** przy niemal tej samej
makro F1, ale nadal ok. **2.5–2.8× wolniejszy od samego MOG2**.
Rzadki LK/ROI ogranicza liczbę śledzonych punktów, lecz gubi dużą
część obiektu: bardzo wysoka precision na `highway` nie rekompensuje
utraty recall. Nie wybieramy go jako domyślnego wariantu.

Pomiar czasu obejmuje koszt właściwy dla każdej metody w jednym
przebiegu na lokalnym CPU; wartości są zależne od obciążenia sprzętu.
Nie testowano GPU. Zwykły dense Farnebäck nie może liczyć tylko
oderwanych pikseli foreground bez ich sąsiedztwa — dlatego ROI użyto
do wyboru rzadkich cech, a nie jako maski nakładanej na wejście flow.

Powtórzenie:

```
python cdnet_benchmark.py ../data/cdnet2014/baseline/highway ../data/cdnet2014/dynamicBackground/canoe --output benchmark_reports/cdnet_roi_subsample_highway_canoe.json
```

To nadal wykrywanie ruchu/tła w CDnet, nie diagnostyka uszkodzeń
obrazu. Ocena, czy wariant oszczędny uogólnia się poza te sekwencje,
wymaga następnych wcześniej niewidzianych nagrań.
