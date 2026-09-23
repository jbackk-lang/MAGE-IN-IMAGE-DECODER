# CDnet 2014 — nowe sekwencje `highway` i `canoe`

Po eksploracji na `pedestrians` i `fountain01` wybrano **bez dalszej
zmiany algorytmu lub progów** dwa wcześniej niewidziane nagrania:
`baseline/highway` i `dynamicBackground/canoe`. Testowano pełne
sekwencje zgodnie z temporal ROI i przestrzennym ROI CDnet, z
etykietami 0/255 jako jedynymi ocenianymi. To test świeżych sekwencji,
ale wciąż tylko dwóch z całego zbioru; nie stanowi dowodu skuteczności
w innych kategoriach ani w zadaniu wykrywania usterek obrazu.

| Sekwencja | Metoda | Precision | Recall | F1 | Średni czas/klatkę |
| --- | --- | ---: | ---: | ---: | ---: |
| highway (1231 ocenianych klatek) | MOG2 | 0.7133 | 0.9109 | 0.8001 | 7.9 ms |
| highway | MOG2 ∩ pole wektorów | **0.9050** | 0.7301 | **0.8082** | 31.9 ms |
| canoe (390 ocenianych klatek) | MOG2 | 0.3456 | **0.8038** | 0.4834 | **7.9 ms** |
| canoe | MOG2 ∩ pole wektorów | **0.4062** | 0.7998 | **0.5388** | 29.8 ms |

Makro F1: **0.6417 → 0.6735** (+0.0318) po dodaniu wektorów.
W obu sekwencjach rośnie precision, kosztem recall (mocniej na
`highway`). Czas rośnie ok. **3.8–4.0×** względem samego MOG2; pomiar
czasu to pojedynczy przebieg na tej maszynie, nie benchmark sprzętowy.
Wynik `canoe` nadal jest umiarkowany, nie „rozwiązany”.

Pełny lokalny raport (po uruchomieniu poniższej komendy):
`benchmark_reports/cdnet_independent_highway_canoe.json`.

```
python download_cdnet.py highway
python download_cdnet.py canoe
python cdnet_benchmark.py ../data/cdnet2014/baseline/highway ../data/cdnet2014/dynamicBackground/canoe --output benchmark_reports/cdnet_independent_highway_canoe.json
```

Źródła surowych archiwów i SHA-256:

| Sekwencja | URL | SHA-256 archiwum |
| --- | --- | --- |
| highway | https://changedetection.net/static/dataset/baseline/highway.zip | `44878b640a1c8c9e9a5fb5c447c596c7d21ccdf032dfc3f869313375fb1b210c` |
| canoe | https://changedetection.net/static/dataset/dynamicBackground/canoe.zip | `60f6fca6b03293fb1de81a5ce16167506180395f83a13abd1166c8052b2cea2f` |

Surowe klatki i maski są w `C:\Users\jback\Downloads\a\data\cdnet2014`,
**poza repozytorium**. Pozostałe dwa wcześniej pobrane nagrania
(`pedestrians`, `fountain01`) przeniesiono do tego samego magazynu.

Źródło opisu etykiet i struktury danych:
https://changedetection.net/dataset2014/ .
