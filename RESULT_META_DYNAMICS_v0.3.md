# RESULT — META_DYNAMICS v0.3 (ρ per region, UCSD Ped2) — NOT SUPPORTED

Pre-rejestracja: `PREREG_META_DYNAMICS_v0.3.md` (commit d22ae56, aneks techniczny a868f0b). Bramka syntetyczna 10/10
przed oceną; kalibracja odtworzyła k = 5,0. Jednorazowa ocena na odłożonych klipach Test006–Test012
(pełne liczby: `RESULT_META_DYNAMICS_v0.3.json`):

| Klip | klatki gt | wykrycie gt | alarmy na non-gt |
| --- | --- | --- | --- |
| Test006 | 159 | 0,79 | 1,00 (21 klatek) |
| Test007 | 135 | 1,00 | 0,24 (45 klatek) |
| Test008 | 180 | 0,72 | — |
| Test009 | 120 | 0,03 | — |
| Test010 | 150 | 0,02 | — |
| Test011 | 180 | 0,04 | — |
| Test012 | 93 | 0,00 | 0,45 (87 klatek) |

Łącznie: wykrycie gt 0,40, alarmy non-gt 0,46, Fisher (gt > non-gt) p = 0,95, klipy spełniające (d): 1 z 7.
Żadne kryterium nie jest spełnione → **NOT SUPPORTED**.

Interpretacja: na zbiorze deweloperskim (Test001–005) ρ per region działało (wykrycie 0,70 przy 1% alarmów), a na
nowych klipach nie — w Test006/007/012 flaga zapala się także na normalnych klatkach, a w Test009–011 prawie nie
reaguje na anomalie. Referencja per region z Train001–012 nie przenosi się na te sceny; sukces na zbiorze
deweloperskim był dopasowaniem do oglądanych danych. Zgodnie z pre-rejestracją nie stroimy k po ocenie.
