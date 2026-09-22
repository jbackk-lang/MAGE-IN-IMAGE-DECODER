# CASIA v2 splicing/copy-move sample (4 obrazy + ground truth)

Źródło: mirror `namtpham/casia2groundtruth`
(https://github.com/namtpham/casia2groundtruth), katalog `Samples/`.

Oryginalny zbiór CASIA v2 (Institute of Automation, Chinese Academy of
Sciences) nie jest już hostowany na oficjalnym serwerze; autor mirror
repo udostępnia grunt prawdy (maski) oraz 4 przykładowe pary obraz+maska
w `Samples/` jako publicznie dostępną próbkę.

Pliki:
- `Tp_D_CRN_M_N_pla00035_pla00033_10997.jpg` + `..._gt.png` — splicing
- `Tp_D_CRN_S_N_nat00033_cha00086_11502.jpg` + `..._gt.png` — splicing
- `Tp_S_NNN_S_O_pla00077_pla00077_11212.jpg` + `..._gt.png` — copy-move
- `Tp_S_NRN_S_N_pla00005_pla00005_10937.jpg` + `..._gt.png` — copy-move

Konwencja nazw: `Tp_D_` = tampered, different source (splicing);
`Tp_S_` = tampered, same source (copy-move). Maski `_gt.png`: binarne
(0=autentyczne, 255=zmanipulowany region).

Cytowanie (oryginalna publikacja CASIA v2):
J. Dong, W. Wang, T. Tan, "CASIA Image Tampering Detection Evaluation
Database," IEEE China Summit and International Conference on Signal and
Information Processing, 2013.

Użycie: wyłącznie do badań/testów niekomercyjnych, zgodnie z warunkami
oryginalnego zbioru. Patrz `RESULT_CONTOUR_CURVATURE_v0.1.md` w katalogu
głównym repo dla wyniku testu na tym podzbiorze (N=4, jawnie niska moc
statystyczna).
