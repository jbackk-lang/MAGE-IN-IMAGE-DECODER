# UCSD Ped2 — zbiór KALIBRACYJNY (Test004, Test005)

Osobny od `data/ucsd_ped2/` (który zawiera Test001-003, używane jako
GŁÓWNY test v0.1/v0.2 — patrz `RESULT_META_DYNAMICS_v0.1.md`). Te dwa
klipy (Test004, Test005) są używane WYŁĄCZNIE do kalibracji stałej progu
`k` w `PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md` — nigdy do oceny
wyniku głównego testu, żeby uniknąć wycieku danych (kalibracja na tym
samym zbiorze, na którym potem ocenia się wynik, unieważniłaby test).

Pochodzenie i konwersja identyczne jak `data/ucsd_ped2/README.md`
(git clone mirrora `junaidwahid/UCSD-Anomaly-dataset`, TIFF→PNG
bezstratnie). `Test/ground_truth.json` — zakresy `gt_frame` (1-indeksowane,
włącznie) z `UCSDped2.m`: Test004=[31,180], Test005=[1,129].
