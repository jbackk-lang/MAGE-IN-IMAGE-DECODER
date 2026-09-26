# Aneks 0 do CLAIM_AUDIT_PREREG.md — poprawka techniczna przed pierwszym wynikiem

Pierwsze uruchomienie `recompute_mage.py local` (commit 2061b1c) zakończyło się po ~114 s bez komunikatu i bez pliku
wynikowego (prawdopodobnie proces zabity przez limit pamięci maszyny wirtualnej — wszystkie kroki i pytest w jednym
procesie). Skrypt podzielono na kroki (`local meta|calib|contour|tests`), bez zmiany obliczeń. Podczas diagnozy
uruchomiono osobno `real_meta_dynamics_ped2.run_real_test`, `calibrate_rho_threshold.run_calibration` i
`real_contour_curvature_casia2.run_real_test` i obejrzano ich wyniki (p Test001–003, wybrane k, p dla 4 obrazów CASIA)
— zanim ten aneks został zapisany. Karty i reguły nie zostały zmienione.
