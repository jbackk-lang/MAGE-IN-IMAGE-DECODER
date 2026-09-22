# RESULT — META_DYNAMICS_v0.2 (kalibracja k) — ZATRZYMANE NA BRAMCE

Status: **STOP przed danymi realnymi** — bramka syntetyczna (PREREG_META_DYNAMICS_v0.2.md
sekcja 2) nie przeszła w pełni. `Test001-003` NIE zostały dotknięte tym
wynikiem k=2.0. Zgłoszone w całości, bez dalszego dostrajania.

## 1. Kalibracja k — wynik (PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md)

Sweep po siatce `{3.5, 3.0, 2.5, 2.0, 1.5, 1.0, 0.75, 0.5}` na zbiorze
kalibracyjnym (Test004, Test005, rozłącznym z Test001-003):

| k | false_alarm (kalibr. neg. ctrl) | sensitivity (calib) | non_gt_rate (calib) | PASSES |
|---|---|---|---|---|
| 3.5 | 0.017 | 0.004 | 0.000 | NIE (sensitivity<0.10) |
| 3.0 | 0.017 | 0.014 | 0.000 | NIE (sensitivity<0.10) |
| 2.5 | 0.017 | 0.036 | 0.000 | NIE (sensitivity<0.10) |
| **2.0** | **0.083** | **0.140** | **0.000** | **TAK** |
| 1.5 | 0.267 | 0.269 | 0.000 | NIE (false_alarm≥0.15) |
| 1.0 | 0.400 | 0.538 | 0.039 | NIE (false_alarm≥0.15) |
| 0.75 | 0.533 | 0.670 | 0.255 | NIE (false_alarm≥0.15) |
| 0.5 | 0.617 | 0.781 | 0.392 | NIE (false_alarm≥0.15) |

`k=2.0` wybrane wg zamrożonej reguły (największe k spełniające
wszystkie 3 warunki, sekcja 5 PREREG kalibracji).

## 2. Bramka v0.2 (PREREG_META_DYNAMICS_v0.2.md sekcja 2) — CZĘŚCIOWA PORAŻKA

Dwa niezależne testy syntetyczne z `k=2.0`:

- **Kontrola pozytywna** (`test_positive_control_k2_...`): **PRZESZŁA** —
  Λ i ρ podwyższone w oknie wstrzykniętego ruchu.
- **Kontrola negatywna** (`test_negative_control_k2_...`, ten sam
  scenariusz syntetyczny co oryginalna kontrola v0.1: `seed=10`
  referencja, `seed=20` test, 64×64, INNY niż scenariusz użyty w samej
  kalibracji): **NIE PRZESZŁA** — `false_alarm_rate = 0.1500`, dokładnie
  na granicy progu `<0.15` (formalnie: `0.15 < 0.15` jest fałszywe).

## 3. Interpretacja — dlaczego to jest realny STOP, nie przypadkowa usterka testu

Kalibracja (sekcja 1) zmierzyła `false_alarm_rate=0.083` dla `k=2.0` na
WŁASNYM scenariuszu kontroli negatywnej (seed=98/99). Ten sam próg,
zastosowany do INNEGO, wcześniej niewidzianego podczas kalibracji
scenariusza szumu (seed=10/20 z oryginalnego `PREREG_META_DYNAMICS_v0.1.md`),
daje `0.150` — niemal dwukrotnie więcej. To pokazuje, że `k=2.0` nie ma
komfortowego marginesu: stopa fałszywych alarmów jest silnie wrażliwa na
to, KTÓRA konkretna realizacja szumu jest testowana, nie jest stabilną
własnością samego progu. Dokładnie to jest powód, dla którego
`PREREG_META_DYNAMICS_v0.2.md` §2 wymagał ponownego przejścia bramki z
NOWYM `k`, zamiast zakładać, że przejście kalibracji wystarcza.

Zgodnie z zasadą stop-if-failed (ta sama dyscyplina co
`chrono_sphere_bridge`/`chrono_modal_geometry_bridge` w GIA-TIMDR):
**nie przechodzimy do `Test001-003`**. Podniesienie `k` z powrotem (np.
do 2.5, które przeszło kalibrację inaczej) byłoby dostrajaniem po
zobaczeniu wyniku bramki — zabronione przez `PREREG_META_DYNAMICS_v0.2.md`
§5 ("to jest OSTATNIA runda dostrajania progu w tej gałęzi").

## 4. Wniosek

Prosty próg MAD (mediana+k·MAD) na Λ/E dla ρ **nie daje się sensownie
skalibrować** w badanym zakresie `k` — albo jest martwy (k≥2.5, prawie
zawsze rho=0), albo niestabilny na granicy działania (k=2.0, różne
realizacje szumu dają wynik raz po jednej, raz po drugiej stronie
progu bramki), albo wyraźnie zbyt czuły (k≤1.5, false_alarm≥0.267).
Zgodnie z `PREREG_META_DYNAMICS_v0.2.md` §5: to NIE jest powód do
kolejnej rundy kalibracji tej samej definicji `ρ` — dalsza praca nad ρ
(jeśli w ogóle) wymagałaby innej definicji progu (np. percentylowej
zamiast MAD, albo osobnych progów per-region zamiast jednego globalnego
Λ/E), nie kolejnego sweepu `k`.

Λ (niezmieniona względem v0.1, nie zależy od `k`) zachowuje swój
wcześniejszy, mieszany wynik z `RESULT_META_DYNAMICS_v0.1.md` — duży,
istotny efekt na 1 z 3 klipów (Test002), brak efektu na pozostałych.

**Ocena całościowa gałęzi META_DYNAMICS-na-wideo (v0.1+v0.2): NOT
SUPPORTED dla ρ, trop częściowy (nie potwierdzony) dla Λ.**
