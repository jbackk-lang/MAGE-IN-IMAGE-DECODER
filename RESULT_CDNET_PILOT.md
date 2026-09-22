# CDnet 2014 — pilotaż porównania masek ruchu

To porównanie dotyczy **pikselowego wykrywania ruchu/tła**, nie wykrywania
manipulacji obrazu ani zdarzeń anomalnych. Użyto oficjalnych sekwencji
`baseline/pedestrians` i `dynamicBackground/fountain01`. Dane pobrane przez
`download_cdnet.py` pozostają lokalne i są ignorowane przez Git; szczegółowy
raport JSON powstaje po uruchomieniu polecenia poniżej.

```
python download_cdnet.py pedestrians fountain01
python cdnet_benchmark.py data/cdnet2014/baseline/pedestrians data/cdnet2014/dynamicBackground/fountain01 --output benchmark_reports/cdnet_two_sequences.json
```

| Sekwencja | Metoda | F1 | Precision | Recall | Średni czas/klatkę |
| --- | --- | ---: | ---: | ---: | ---: |
| pedestrians | DefectScanner | 0.6291 | 0.5631 | 0.7127 | 16.50 ms |
| pedestrians | DefectScanner + TwistDetector | 0.6097 | 0.5628 | 0.6650 | 75.77 ms |
| pedestrians | MOG2 | **0.6798** | 0.5185 | 0.9869 | **5.56 ms** |
| fountain01 | DefectScanner | 0.0136 | 0.0071 | 0.1896 | 21.22 ms |
| fountain01 | DefectScanner + TwistDetector | 0.0142 | 0.0074 | 0.1683 | 97.18 ms |
| fountain01 | MOG2 | **0.0392** | 0.0201 | 0.8311 | **6.05 ms** |

Makrośrednia F1 z dwóch sekwencji: DefectScanner **0.3214**,
DefectScanner + TwistDetector **0.3119**, MOG2 **0.3595**.
Przebieg obejmował pełne zakresy klatek i odpowiednio 800 oraz 785
klatek ocenianych w temporal ROI. Piksele spoza przestrzennego ROI i
etykiety niejednoznaczne zostały wyłączone z metryk.

Wniosek: w tym pilotażu połączenie detektorów **nie poprawiło F1** i było
znacznie wolniejsze. Na fontannie wszystkie trzy metody mają bardzo słabą
precyzję. To dwa przykłady, nie reprezentatywna ocena całego CDnet;
wynik nie dowodzi ani ogólnej przewagi MOG2, ani nieprzydatności I²D do
innych zadań. Warto dalej porównać więcej kategorii i osobno mierzyć
zadanie, do którego detektory I²D były projektowane.

Źródło danych: https://changedetection.net/dataset2014/ .
