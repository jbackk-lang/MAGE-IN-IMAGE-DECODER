# Eksploracja pola wektorowego na CDnet 2014

Cel: sprawdzić, czy pola wektorów ruchu z kolejnych klatek pomagają w
segmentacji foreground. To **nie** jest wynik niezależnego testu:
`pedestrians` i `fountain01` były już oglądane w pilotażu, a warianty
powstały po obejrzeniu wcześniejszych wyników. Obie sekwencje liczone
w pełnym temporal ROI, z tą samą definicją ważnych pikseli co w
[`RESULT_CDNET_PILOT.md`](RESULT_CDNET_PILOT.md).

```
python cdnet_benchmark.py ../data/cdnet2014/baseline/pedestrians ../data/cdnet2014/dynamicBackground/fountain01 --output benchmark_reports/cdnet_two_sequences_vector_mog2.json
```

| Metoda | F1 pedestrians | F1 fountain01 | Makro F1 | Czas pedestrians | Czas fountain01 |
| --- | ---: | ---: | ---: | ---: | ---: |
| DefectScanner (blok) | 0.6291 | 0.0136 | 0.3214 | 9.9 ms | 22.0 ms |
| DefectScanner ∩ zmienione piksele | 0.5632 | 0.0129 | 0.2881 | ~9.9 ms | ~22.1 ms |
| DefectScanner ∩ TwistDetector | 0.6097 | 0.0142 | 0.3119 | 55.1 ms | 62.8 ms |
| Spójne pole wektorów | 0.2572 | 0.0102 | 0.1337 | 18.8 ms | 22.3 ms |
| DefectScanner ∩ pole wektorów | 0.6161 | 0.0164 | 0.3162 | 25.5 ms | 54.7 ms |
| MOG2 | 0.6798 | 0.0392 | 0.3595 | 3.7 ms | 7.0 ms |
| MOG2 ∩ pole wektorów | **0.7771** | **0.0701** | **0.4236** | 19.3 ms | 40.1 ms |

Wektor to przepływ optyczny `(vx, vy)` między dwiema klatkami, obliczany
metodą Farnebäcka na obrazie zmniejszonym o połowę. Maska zaznacza blok
16×16, jeżeli długość średniego wektora wynosi co najmniej 1 piksel
na klatkę, a zgodność kierunków co najmniej 0.75. Sumy/średnie bloków
liczy NumPy tablicowo, wzorem architektury `Synoptyk-v3`; samo użycie
wektorów **nie** gwarantuje przyspieszenia. `∩` oznacza logiczne AND
dwóch masek, bez dopasowywania wag do etykiet CDnet.

Co działa w tym ograniczonym porównaniu: połączenie MOG2 z polem
wektorowym poprawia precision i F1 w obu sekwencjach. Co nie działa:
filtrowanie masek pojedynczych pikseli obniża F1, a samo pole wektorowe
ma niski F1. Koszt MOG2 ∩ wektory jest ok. 5–6× większy od samego MOG2;
to nie jest przyspieszenie systemu. Na `fountain01` nawet najlepszy
wariant ma F1=0.0701, nadal słaby wynik bezwzględny.

Wynik wymaga niezależnych sekwencji, najlepiej także innych kategorii
CDnet, zanim można mówić o uogólnieniu. Nie ma tu twierdzenia o
wykrywaniu uszkodzeń ani implementacji geometrycznej gałęzi G TIMDR.
