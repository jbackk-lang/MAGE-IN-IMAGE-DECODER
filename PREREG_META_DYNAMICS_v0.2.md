# PREREG — META_DYNAMICS_v0.2 (druga runda, k przekalibrowane)

Status: ZAMROŻONE PRZED ponownym uruchomieniem testu na `Test001-003`.
Zmienia WYŁĄCZNIE wartość stałej `k` względem v0.1 — wszystko inne
(wzory Λ/τ/ρ, siatka 4×4, okno τ, dane referencyjne, dane testowe, plan
statystyczny) jest IDENTYCZNE z `PREREG_META_DYNAMICS_v0.1.md` i nie jest
tu powtarzane w całości.

## 1. Co się zmienia względem v0.1

`k = 2.0` (zamiast `3.5`), wybrane w
`PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md` na ODDZIELNYM zbiorze
kalibracyjnym (`Test004`, `Test005`) — `Test001-003` (dane tego
dokumentu) NIE były dotykane podczas kalibracji.

## 2. Bramka syntetyczna (WYMAGANA ponownie, z nowym k)

Kontrola pozytywna i negatywna z v0.1 (`test_meta_dynamics_v1.py`) muszą
przejść RÓWNIEŻ z `k=2.0` — nie zakładamy, że przejście z `k=3.5`
gwarantuje przejście z niższym, bardziej czułym progiem (niższe `k` =
łatwiej o fałszywy alarm na kontroli negatywnej, patrz wynik kalibracji:
`k=1.5` już łamie bramkę `false_alarm_rate<0.15`). Nowe testy:
`test_positive_control_k2_...`, `test_negative_control_k2_...` w
`test_meta_dynamics_v1.py` — DOPISANE obok istniejących (k=3.5)
testów, nie zastępujące ich (historia obu wersji zostaje widoczna).

## 3. Test główny (niezmieniony plan statystyczny z v0.1 §6)

`Test001-003`, referencja `Train001-004` (te same co v0.1). Mann-Whitney
U + rank-biserial na Λ (WYNIK IDENTYCZNY jak w v0.1 — Λ nie zależy od
`k`, więc te liczby nie zmienią się między v0.1 a v0.2; powtarzane tu
tylko dla kompletności raportu). Fisher dokładny na ρ, teraz z `k=2.0` —
JEDYNA część, która może dać inny wynik niż v0.1. Bonferroni,
α_corr=0.05/6 jak w v0.1.

## 4. Reguła decyzji (zamrożona PRZED wynikiem)

- **SUPPORTED**: ρ istotne (Bonferroni) na ≥2 z 3 klipów, w kierunku
  gt>non-gt.
- **CZĘŚCIOWO SUPPORTED**: ρ istotne na dokładnie 1 z 3 klipów, w
  kierunku gt>non-gt.
- **NOT SUPPORTED**: ρ nieistotne na żadnym klipie, LUB istotne w
  kierunku PRZECIWNYM (gt<non-gt — co sugerowałoby, że próg łapie coś
  innego niż anomalie).

Λ oceniana OSOBNO, opisowo (już ma swój wynik z v0.1, niezmieniony) — nie
wchodzi do powyższej reguły SUPPORTED/NOT, bo nie zależy od tej
kalibracji.

## 5. Co dzieje się PO tym dokumencie

Niezależnie od wyniku — to jest OSTATNIA runda dostrajania progu w tej
gałęzi. Jeśli NOT SUPPORTED nawet z przekalibrowanym `k`, wniosek jest:
prosty próg MAD na Λ/E (niezależnie od wartości `k`) nie niesie
sygnału specyficznego dla ρ na tym materiale — dalsza praca (jeśli
w ogóle) wymagałaby innej definicji ρ, nie kolejnej kalibracji tej samej
definicji.
