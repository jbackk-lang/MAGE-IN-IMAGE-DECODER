# RESULT — META_DYNAMICS_v0.1 na UCSD Ped2

Status: **MIESZANY / CZĘŚCIOWO NEGATYWNY** — zgłoszony w całości, bez
retuningu po zobaczeniu wyniku (protokół z `PREREG_META_DYNAMICS_v0.1.md`).
ρ nie działa na tych danych; Λ replikuje się w 1 z 3 klipów.

## 1. Kontrole syntetyczne (bramka) — PRZESZŁY

Obie kontrole z PREREG sekcji 4 przeszły (`test_meta_dynamics_v1.py`,
6/6 testów): kontrola pozytywna wykryła wstrzyknięty lokalny ruch
(Λ i ρ podwyższone w oknie wstrzyknięcia), kontrola negatywna nie dała
fałszywych alarmów na czystym szumie. Zgodnie z bramką, przeszliśmy do
danych realnych.

## 2. Wynik na realnych danych (UCSD Ped2, Test001-003)

Progi referencyjne (600 klatek treningowych, Train001-004):
`Λ_threshold = 0.4981`, `E_threshold = 45.38` (mediana + 3.5·MAD).

| Klip | n (gt/non-gt) | Λ: gt_mean vs non_gt_mean | Mann-Whitney p | r (rozmiar efektu) | istotne (α=0.0083) | ρ: gt_rate / non_gt_rate |
|---|---|---|---|---|---|---|
| Test001 | 120/60 | 0.304 vs 0.291 | 0.196 | 0.119 (mały) | **NIE** | 0.000 / 0.000 |
| Test002 | 86/94 | **0.242 vs 0.184** | **9.9e-22** | **0.828 (duży)** | **TAK** | 0.000 / 0.000 |
| Test003 | 146/4 | 0.257 vs 0.251 | 0.569 | 0.175 (mały) | NIE | 0.000 / 0.000 |

### ρ (binarna flaga MAD, k=3.5): NIEDZIAŁAJĄCA na tych danych

Wskaźnik anomalii `ρ=1` NIGDY nie zadziałał — ani w grupie gt, ani w
non-gt, w ŻADNYM z 3 klipów. Diagnoza (nie zgadywanie): sprawdzono
rozkłady wprost — `E_test002` (max=38.41) i `Λ_test002` (max=0.299) NIE
PRZEKRACZAJĄ progów referencyjnych (`E_threshold=45.38`,
`Λ_threshold=0.498`) NAWET W SZCZYCIE. Stała `k=3.5` (mediana+k·MAD),
przeniesiona bez zmian z domeny wibracji/sejsmiki (`ROBUST_K` w całym
ekosystemie TIMDR), okazuje się dla tego sygnału wideo zbyt luźna —
rozstęp Λ/E między klatkami "spokojnymi" i "ruchliwymi" w tym materiale
jest mniejszy względem swojej własnej medianowej wartości niż w
sygnałach wibracyjnych, na których `k=3.5` była pierwotnie dobrana. To
NIE jest błąd kodu (zweryfikowano wprost na rozkładach) — to
miskalibracja stałej międzydomenowej, dokładnie ten rodzaj ryzyka, przed
którym ostrzegało zastrzeżenie #2 w PREREG. Świadomie NIE obniżamy `k`
teraz, żeby "naprawić" wynik — to byłby retuning po zobaczeniu wyniku,
zabroniony przez własny protokół tego dokumentu. Rekalibracja `k` (albo
inna definicja progu, np. percentylowa zamiast MAD) to zadanie na
osobną, nową wersję (v0.2) z własnym PREREG.

### Λ (ciągła, Mann-Whitney U): replikuje się w 1 z 3 klipów

Test002 daje zdecydowany, przetrwały korektę Bonferroniego wynik w
PRZEWIDYWANYM kierunku (klatki anomalne mają WYŻSZĄ koncentrację
przestrzenną ruchu). Test001 i Test003 nie dają efektu. To NIE jest
potwierdzony wynik w sensie `timdr-signal-framework` (brak spójności
między przypadkami — dokładnie zastrzeżenie #3 z PREREG: "wynik
pozytywny tu jest tropem wymagającym replikacji, nie ostatecznym
dowodem"). Trzy klipy testowe to za mała próba, żeby rozstrzygnąć, czy
Test002 jest prawdziwym sygnałem, czy przypadkiem sprzyjającej sceny
(w Test002 anomalia trwa krócej i zajmuje inny fragment klatek niż w
pozostałych dwóch — możliwe, że rodzaj/tor ruchu anomalii w tym
konkretnym klipie akurat pasuje do założenia "ruch skupiony w jednym
regionie", podczas gdy w Test001/003 anomalia porusza się bardziej
rozproszenie po scenie, co Λ z definicji nie wychwytuje).

## 3. Uczciwa ocena całości

Formalizm Λ-τ-ρ przeniesiony z sygnałów wibracyjnych na pole ruchu wideo
NIE dał tu ogólnego, spójnego sygnału detekcji anomalii — 1 z 3 klipów
z dużym efektem na Λ, ρ całkowicie nieaktywna z powodu miskalibrowanej
stałej. To jest wynik NEGATYWNY/MIESZANY, kompletny i wartościowy sam w
sobie (zgodnie z `timdr-signal-framework` §2 punkt 6) — nie "trzeba było
spróbować inaczej, żeby zadziałało". Najbardziej prawdopodobny,
nie-numerologiczny następny krok (JEŚLI ktoś zdecyduje się kontynuować
tę gałąź): v0.2 z progiem percentylowym zamiast MAD·k (percentyl
dobrany na REFERENCJI, nie na wyniku testowym) oraz sprawdzeniem, czy
brak efektu w Test001/003 wynika z tego, że tamte anomalie faktycznie
NIE są przestrzennie skoncentrowane (do zweryfikowania wizualnie na
maskach pikselowych oryginalnego datasetu, nieużytych w v0.1).

## 4. Zakres tego wyniku

3 klipy testowe, 4 klipy treningowe, jedna scena (Ped2), jedna siatka
(4×4). Nie testowano Ped1 (inna scena, dystorsja perspektywy). Wynik nie
uogólnia się automatycznie na inne sceny/siatki/wielkości okna.
