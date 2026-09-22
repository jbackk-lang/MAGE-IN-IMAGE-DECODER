"""test_meta_dynamics_ped2_real.py -- test regresyjny na realnym podzbiorze
UCSD Ped2 (data/ucsd_ped2/). Zamraza wynik opisany w
RESULT_META_DYNAMICS_v0.1.md -- MIESZANY: Test002 daje duzy, istotny
efekt na Lambda w przewidywanym kierunku; Test001/Test003 nie daja
efektu; rho nigdy nie wyzwala sie na tych danych (miskalibrowana stala
k=3.5, patrz RESULT sekcja 2). Ten test NIE jest pozytywnym testem
"dziala" -- jest regresja pilnujaca, ze przyszle zmiany w kodzie nie
zmienia po cichu tego (juz przeanalizowanego, wyjasnionego) zachowania
bez swiadomej decyzji."""
import os

import pytest

from real_meta_dynamics_ped2 import DATA_DIR, run_real_test


def _data_exists():
    return os.path.exists(os.path.join(DATA_DIR, "Test", "ground_truth.json"))


@pytest.mark.skipif(not _data_exists(), reason="brak podzbioru UCSD Ped2 w data/ucsd_ped2/")
def test_ped2_test002_shows_large_significant_lambda_effect():
    results = run_real_test(verbose=False)
    r = results["Test002"]
    assert r["significant_mannwhitney_bonferroni"] is True
    assert r["effect_size_label"] == "duzy"
    assert r["lambda_gt_mean"] > r["lambda_non_gt_mean"]  # kierunek zgodny z hipoteza PREREG


@pytest.mark.skipif(not _data_exists(), reason="brak podzbioru UCSD Ped2 w data/ucsd_ped2/")
def test_ped2_test001_and_test003_show_no_significant_lambda_effect():
    results = run_real_test(verbose=False)
    for clip in ("Test001", "Test003"):
        assert results[clip]["significant_mannwhitney_bonferroni"] is False


@pytest.mark.skipif(not _data_exists(), reason="brak podzbioru UCSD Ped2 w data/ucsd_ped2/")
def test_ped2_rho_never_triggers_known_miscalibration():
    """Dokumentuje znane, zdiagnozowane ograniczenie (RESULT sekcja 2) --
    jesli ten test kiedys zacznie failowac, to znaczy ze albo dane, albo
    stala ROBUST_K sie zmienily i RESULT.md trzeba zaktualizowac, nie ze
    test jest zly."""
    results = run_real_test(verbose=False)
    for clip in results.values():
        assert clip["rho_gt_rate"] == 0.0
        assert clip["rho_non_gt_rate"] == 0.0
