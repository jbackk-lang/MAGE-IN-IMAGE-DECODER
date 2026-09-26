"""Karty twierdzeń README (MAGE-IN-IMAGE-DECODER) dla tools/claim_audit.py.
Reguły: docs/audit/CLAIM_AUDIT_PREREG.md + aneksy 0 i 1. Przeliczenia: docs/audit/RECOMPUTE_MAGE.json.

v1.1 (po przebiegu 1 i poprawce README): nowe cytaty M2, L0 (+L8), L3, L4, L6 (+L9), T1 (+T5); M5 oparte na historii gita;
R6 z ujawnieniem; „dowodzi” poprzedzone „nie” pomijane w R7b.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "tools"))
from claim_audit import POTWIERDZONE, SPRZECZNE, NIEROZSTRZYGNIETE, UDOKUMENTOWANE, Claim, Result  # noqa: E402

TITLE = "README → META_DYNAMICS, CONTOUR_CURVATURE, dashboard, CDnet, zdrowa referencja, testy (MAGE-IN-IMAGE-DECODER)"
README = "README.md"
PREREG = "docs/audit/CLAIM_AUDIT_PREREG.md"
OUTPUT = "CLAIM_AUDIT.md"
SCOPES = [(r"^### META_DYNAMICS v0.1", r"^```python"), (r"^### CONTOUR_CURVATURE v0.1", r"^```python"),
          (r"^## 🖥️ Dashboard", r"^### Szybkie nakładki"), (r"^### Laboratorium porównań", r"^### Film względem"),
          (r"^### Film względem", r"^## 🧪 Testy"), (r"^## 🧪 Testy", r"^## 📄 Licencja")]
DO_ZLAGODZENIA = "DO ZŁAGODZENIA"


def rc() -> dict:
    return json.loads((HERE / "RECOMPUTE_MAGE.json").read_text(encoding="utf-8"))


def src(name: str) -> str:
    return (REPO / name).read_text(encoding="utf-8")


def rep(name: str) -> dict:
    return json.loads((REPO / "benchmark_reports" / f"{name}.json").read_text(encoding="utf-8"))


def R(ok, value, note=""):
    return Result(POTWIERDZONE if ok else SPRZECZNE, value, note)


def c(x, n=4):
    return f"{x:.{n}f}".replace(".", ",")


def seqs(report: dict) -> dict:
    return {q["sequence"]: q["methods"] for q in report["sequences"]}


def rerun() -> dict:
    return seqs(rc()["cdnet_rerun"])


def f1_equal(names: list[str], report_names: list[str]) -> tuple[bool, list]:
    """R8: F1 z ponownego uruchomienia = raport JSON (4 miejsca) dla podanych sekwencji i wszystkich metod raportu."""
    rr, bad = rerun(), []
    for rn in report_names:
        for s, methods in seqs(rep(rn)).items():
            for m, v in methods.items():
                if s in names and round(rr[s][m]["f1"], 4) != round(v["f1"], 4):
                    bad.append((rn, s, m, round(v["f1"], 4), round(rr[s][m]["f1"], 4)))
    return not bad, bad


def ratio(s, a, b):
    rr = rerun()
    return rr[s][a]["mean_ms_per_processed_frame"] / rr[s][b]["mean_ms_per_processed_frame"]


# ---------------------------------------------------------------- META_DYNAMICS
def _sig():
    r, a = rc()["meta_real"], rc()["meta_real_alpha"]
    return [k for k, v in r.items() if v["mannwhitney_p"] < a], r, a


def m_one_of_three():
    sig, r, a = _sig()
    rho0 = all(v["rho_gt_rate"] == 0 and v["rho_non_gt_rate"] == 0 for v in r.values())
    return R(len(sig) == 1 and len(r) == 3 and rho0, f"istotne: {sig} z {sorted(r)} (α = {c(a)}); ρ = 0 we wszystkich",
             "SUROWE: real_meta_dynamics_ped2.py")


def m_loose():
    r = rc()["meta_real"]
    never = all(v["rho_gt_rate"] == 0 and v["rho_non_gt_rate"] == 0 for v in r.values())
    below = "NIE\nPRZEKRACZAJĄ progów" in src("RESULT_META_DYNAMICS_v0.1.md") or "NIE PRZEKRACZAJĄ" in src("RESULT_META_DYNAMICS_v0.1.md").replace("\n", " ")
    if never and below:
        return Result(SPRZECZNE, "ρ nigdy = 1; maksima Λ/E poniżej progów (RESULT v0.1)",
                      "R12: próg nigdy nieprzekroczony = stała za wysoka (za surowa), nie „za luźna”")
    return R(False, "?", "")


def m_high_v11():
    r = rc()["meta_real"]
    never = all(v["rho_gt_rate"] == 0 and v["rho_non_gt_rate"] == 0 for v in r.values())
    below = "NIE PRZEKRACZAJĄ" in src("RESULT_META_DYNAMICS_v0.1.md").replace("\n", " ")
    return R(never and below, "ρ nigdy = 1; maksima Λ/E poniżej progów (RESULT v0.1)", "R12")


def m_untouched_v11():
    import subprocess
    out = subprocess.run(["git", "-C", str(REPO), "log", "--format=%h", "1231ba9..HEAD", "--", "RESULT_META_DYNAMICS_v0.1.md",
                          "real_meta_dynamics_ped2.py", "test_meta_dynamics_ped2_real.py", "data/ucsd_ped2"],
                         capture_output=True, text=True).stdout.split()
    erratum_only = all("Erratum" in subprocess.run(["git", "-C", str(REPO), "show", h, "--", "RESULT_META_DYNAMICS_v0.1.md"],
                                                   capture_output=True, text=True).stdout for h in out)
    return Result(UDOKUMENTOWANE if (not out or erratum_only) else SPRZECZNE,
                  f"zmiany po v0.2 (1231ba9) w plikach Test001-003: {out or 'brak'}" + (" (tylko erratum)" if out else ""),
                  "DOKUMENT + historia gita")


def l_ten_v11():
    m = re.search(r"METHODS = \((.*?)\)", src("cdnet_benchmark.py"), re.S)
    n = len(re.findall(r'"(\w+)"', m.group(1)))
    return R(n == 10, f"METHODS: {n}", "KOD")


def l_pilot_v11():
    rr = rerun()
    up = {s: rr[s]["defect_twist_fusion"]["f1"] - rr[s]["defect"]["f1"] for s in ("pedestrians", "fountain01")}
    ok = abs(up["pedestrians"] + 0.020) <= 0.0006 and abs(up["fountain01"] - 0.001) <= 0.0006
    return R(ok, "; ".join(f"{k}: {v:+.4f}" for k, v in up.items()), "SUROWE")


def l_rerun_ratio_v11(seqs_, lo, hi):
    rs = [ratio(s_, "mog2_vector_fusion", "mog2") for s_ in seqs_]
    return R(all(lo - 0.05 <= round(x, 1) <= hi + 0.05 for x in rs), f"{c(rs[0], 2)}× i {c(rs[1], 2)}×", "powtórka audytu")


def l_all_reports_v11():
    names = [p.stem for p in (REPO / "benchmark_reports").glob("*.json")]
    ok, bad = f1_equal(["pedestrians", "fountain01", "highway", "canoe"], names)
    return R(ok, f"raporty: {len(names)}; różnice F1: {bad or 'brak'}", "R8")


def t_45_v11():
    t = rc()["tests"]
    return R(t["tests_dir"] == 45 and t["tests_i2d_core"] == 22, f"{t['tests_dir']} testów, {t['tests_i2d_core']} w test_i2d_core.py", "R14")


def t_23_v11():
    t = rc()["tests"]
    return R(t["tests_dir"] - t["tests_i2d_core"] == 23, f"{t['tests_dir'] - t['tests_i2d_core']} pozostałych", "R14")


def m_calib():
    cal = rc()["calibration"]
    d = rc()["dirs"]
    disjoint = bool(d["calibration_clips"]) and not set(d["calibration_clips"]) & {"Test001", "Test002", "Test003"}
    return R(cal["chosen_k"] == 2.0 and disjoint, f"wybrane k = {cal['chosen_k']}; klipy kalibracyjne {d['calibration_clips']}",
             "SUROWE: calibrate_rho_threshold.py")


def m_gate():
    t = src("test_meta_dynamics_v1.py")
    ok = "def test_negative_control_k2_borderline_fails_gate_documented_stop" in t and rc()["tests"]["returncode"] == 0
    return R(ok, "test dokumentujący fałszywy alarm = 0,150 przy bramce < 0,15 przechodzi", "KOD REPO")


def m_untouched():
    s = src("real_meta_dynamics_ped2.py")
    ok = "2.0" not in re.sub(r"#.*", "", s) or "ROBUST_K" in s
    return Result(UDOKUMENTOWANE if ok else NIEROZSTRZYGNIETE, "skrypt Test001-003 bez k = 2,0; zapis w RESULT v0.2",
                  "DOKUMENT + KOD")


def m_partial():
    sig, r, _ = _sig()
    return R(len(sig) == 1, f"{len(sig)} z {len(r)}", "")


def m_dashboard_rho():
    return R("NIE jest alarmem" in src("app.py"), "app.py: „historyczne rho … (NIE jest alarmem)”", "KOD")


# ---------------------------------------------------------------- CONTOUR
def c_section0():
    return R(bool(re.search(r"^#+\s*0[\.\s]", src("PREREG_CONTOUR_CURVATURE_v0.1.md"), re.M)), "sekcja 0 w PREREG", "")


def c_result():
    res = rc()["contour_real"]
    sig = [x["name"] for x in res if x["p_value"] < 0.0125]
    t = rc()["tests"]
    cat = "**CZĘŚCIOWO SUPPORTED**: istotny efekt na części, ale nie większości" in src("PREREG_CONTOUR_CURVATURE_v0.1.md")
    ok = len(res) == 4 and len(sig) == 1 and t["contour"] == 7 and t["returncode"] == 0 and cat
    return R(ok, f"istotne {len(sig)} z {len(res)} ({sig}); testy syntetyczne {t['contour']}", "SUROWE: real_contour_curvature_casia2.py")


def c_casia():
    n = len(rc()["dirs"]["casia_images"])
    return Result(NIEROZSTRZYGNIETE if n == 4 else SPRZECZNE, f"w repo {n} obrazy z maskami",
                  "„jedyny publicznie dostępny” i „nie jest już hostowany” - twierdzenia o świecie, nieweryfikowalne z plików")


# ---------------------------------------------------------------- dashboard
def d_port():
    return R("app.run(debug=True, port=5050)" in src("app.py"), "port 5050", "KOD")


def d_modules():
    a = src("app.py")
    block = a.split("MODULES = {", 1)[1].split("\n}\n", 1)[0]
    st, ex = block.count('"status": "stable"'), block.count('"status": "experimental"')
    return R(st == 5 and ex == 2, f"MODULES: {st} stabilnych + {ex} eksperymentalne", "KOD")


def d_limits():
    a, i = src("app.py"), src("i2d_core.py")
    ok = "UPLOAD_MAX_FRAMES = 300" in a and "UPLOAD_MAX_TOTAL_PIXELS = 12_000_000" in a and "20 * 1024 * 1024" in a \
        and 'raise ValueError(f"Wideo przekracza limit {max_frames} klatek")' in i
    return R(ok, "300 klatek, 12 mln pikseli, 20 MB; load_video rzuca błąd zamiast obcinać", "KOD")


# ---------------------------------------------------------------- CDnet
def l_three():
    m = re.search(r"METHODS = \((.*?)\)", src("cdnet_benchmark.py"), re.S)
    n = len(re.findall(r'"(\w+)"', m.group(1)))
    return R(n == 3, f"METHODS w cdnet_benchmark.py: {n} masek", "KOD")


def l_title():
    return R("dataset2014" in src("README.md"), "zbiór CDnet 2014 (changedetection.net/dataset2014)", "")


def l_labels():
    p = rep("pedestrians")["parameters"]
    ok = p["valid_gt_labels"] == [0, 255] and p["ignored_gt_labels"] == [50, 85, 170] and "temporalROI" in src("cdnet_benchmark.py")
    return R(ok, f"etykiety oceniane {p['valid_gt_labels']}, pomijane {p['ignored_gt_labels']}", "JSON + KOD")


def l_pilot():
    ok_eq, bad = f1_equal(["pedestrians", "fountain01"], ["cdnet_two_sequences"])
    rr = rerun()
    up = {s: rr[s]["defect_twist_fusion"]["f1"] - rr[s]["defect"]["f1"] for s in ("pedestrians", "fountain01")}
    if not ok_eq:
        return R(False, f"F1 różne od raportu: {bad}", "R8")
    if any(v > 0 for v in up.values()):
        return Result(DO_ZLAGODZENIA, "; ".join(f"{s}: fuzja − DefectScanner = {v:+.4f}" for s, v in up.items()),
                      "R10: F1 fuzji wyższy na co najmniej jednej sekwencji (SUROWE, F1 = raport)")
    return R(True, str(up), "R10")


def l_vector():
    ok_eq, bad = f1_equal(["pedestrians", "fountain01"], ["cdnet_two_sequences_vector_mog2"])
    rr = rerun()
    better = all(rr[s]["mog2_vector_fusion"]["f1"] > rr[s]["mog2"]["f1"] for s in ("pedestrians", "fountain01"))
    rs = [ratio(s, "mog2_vector_fusion", "mog2") for s in ("pedestrians", "fountain01")]
    ok = ok_eq and better and all(5 * 0.85 <= x <= 6 * 1.15 for x in rs)
    return R(ok, f"F1 = raport: {ok_eq}; stosunek czasu {c(rs[0], 1)}× i {c(rs[1], 1)}×", "R8, R9" + (f"; {bad}" if bad else ""))


def l_same_thresholds():
    a, b = rep("cdnet_two_sequences_vector_mog2")["parameters"], rep("cdnet_independent_highway_canoe")["parameters"]
    new = not {"highway", "canoe"} & set(seqs(rep("cdnet_two_sequences_vector_mog2")))
    return R(a == b and new, "parametry raportów identyczne; highway/canoe nieużyte wcześniej", "JSON")


def l_independent():
    ok_eq, bad = f1_equal(["highway", "canoe"], ["cdnet_independent_highway_canoe"])
    rr = rerun()
    better = all(rr[s]["mog2_vector_fusion"]["f1"] > rr[s]["mog2"]["f1"] for s in ("highway", "canoe"))
    rs = [ratio(s, "mog2_vector_fusion", "mog2") for s in ("highway", "canoe")]
    ok = ok_eq and better and all(3.8 * 0.85 <= x <= 4.0 * 1.15 for x in rs)
    return R(ok, f"F1 = raport: {ok_eq}; stosunek czasu {c(rs[0], 1)}× i {c(rs[1], 1)}×", "R8, R9" + (f"; {bad}" if bad else ""))


def l_roi():
    ok_eq, bad = f1_equal(["highway", "canoe"], ["cdnet_roi_subsample_highway_canoe"])
    rr = rerun()
    keep = all(rr[s]["mog2_cached_flow_2"]["f1"] >= 0.98 * rr[s]["mog2_vector_fusion"]["f1"] for s in ("highway", "canoe"))
    lose = all(rr[s]["mog2_sparse_lk"]["recall"] <= 0.6 * rr[s]["mog2_vector_fusion"]["recall"] for s in ("highway", "canoe"))
    rs = [ratio(s, "mog2_vector_fusion", "mog2_cached_flow_2") for s in ("highway", "canoe")]
    ok = ok_eq and keep and lose and all(1.6 * 0.85 <= x <= 1.6 * 1.15 for x in rs)
    return R(ok, f"F1 = raport: {ok_eq}; co 2 klatki zachowuje F1: {keep}; LK traci recall: {lose}; przyspieszenie "
             f"{c(rs[0], 2)}× i {c(rs[1], 2)}×", "R8, R9, R11" + (f"; {bad}" if bad else ""))


# ---------------------------------------------------------------- zdrowa referencja
def v_p90():
    return R("np.percentile(magnitude, 90)" in src("vector_reference.py"), "percentyl 90 długości wektorów", "KOD")


def v_split():
    s = src("vector_reference.py")
    return R("int(len(features) * 0.6)" in s, "podział 0,6 / 0,4", "KOD; kod wymusza też co najmniej 12 par kalibracyjnych "
             "(max(12, …)), więc dla krótkich filmów podział nie jest dokładnie 60/40")


# ---------------------------------------------------------------- testy
def t_22():
    t = rc()["tests"]
    return R(t["tests_dir"] == 22, f"`pytest tests/`: {t['tests_dir']} testów (w tym {t['tests_i2d_core']} w test_i2d_core.py)", "R14")


def t_11():
    t = rc()["tests"]
    ok = t["meta"] == 11 and "K_V02 = 2.0" in src("test_meta_dynamics_v1.py")
    return R(ok, f"{t['meta']} testów", "R14")


def t_7():
    return R(rc()["tests"]["contour"] == 7, f"{rc()['tests']['contour']} testów", "R14")


def t_n4():
    return R(len(rc()["dirs"]["casia_images"]) == 4, "4 obrazy", "")


CLAIMS = [
    Claim("M1", "na realnych danych tylko 1 z 3 klipów testowych dał istotny efekt na Λ, a binarna flaga ρ nie zadziałała w ogóle", m_one_of_three),
    Claim("M2", "(stała progowa `k=3.5` okazała się zbyt wysoka - Λ i E nie przekroczyły progu nawet w szczycie, więc flaga "
                "nie miała szansy zadziałać)", m_high_v11),
    Claim("M3", "skalibrowało `k=2.0` na osobnym zbiorze (`data/ucsd_ped2_calibration/`, rozłącznym z Test001-003)", m_calib),
    Claim("M4", "`k=2.0` nie ma bezpiecznego marginesu — na innym scenariuszu syntetycznym niż ten użyty w kalibracji fałszywy "
                "alarm wychodzi dokładnie na granicy progu", m_gate),
    Claim("M5", "Zgodnie z protokołem stop-if-failed, `Test001-003` NIE zostały ponownie dotknięte", m_untouched_v11),
    Claim("M6", "Λ pozostaje częściowym tropem (1 z 3 klipów, niepotwierdzone)", m_partial),
    Claim("M7", "Dashboard pokazuje historyczne `rho` wyłącznie informacyjnie; nie używa go jako zwalidowanego alarmu", m_dashboard_rho),
    Claim("C1", "sekcja 0", c_section0),
    Claim("C2", "**CZĘŚCIOWO SUPPORTED, niska moc (N=4)**: bramka syntetyczna przeszła czysto (7/7 testów), ale na realnych "
                "danych tylko 1 z 4 obrazów dał istotny efekt (po korekcie Bonferroniego)", c_result),
    Claim("C3", "jedyny publicznie dostępny podzbiór CASIA v2 z ground truth ma tylko 4 przykłady (oryginalny zbiór nie jest "
                "już hostowany publicznie)", c_casia),
    Claim("D1", "Otwiera się na `http://localhost:5050`", d_port),
    Claim("D2", "Strona per moduł (wszystkie 7: 5 stabilnych detektorów + META_DYNAMICS + CONTOUR_CURVATURE)", d_modules),
    Claim("D3", "Wgrywane wideo ma limit 300 klatek, 12 mln pikseli łącznie i 20 MB; zbyt duży plik jest odrzucany jawnie, "
                "a nie po cichu obcinany", d_limits),
    Claim("L0", "`cdnet_benchmark.py` porównuje na tych samych klatkach 10 masek: trzy bazowe", l_ten_v11),
    Claim("L8", "i 7 wariantów z polem wektorów ruchu", l_ten_v11),
    Claim("L1", "### Laboratorium porównań CDnet 2014", l_title),
    Claim("L2", "piksele z etykietami 0 (tło) lub 255 (ruch), wewnątrz `ROI.bmp`; etykiety 50, 85 i 170 są pomijane", l_labels),
    Claim("L3", "W tym pilotażu fuzja nie poprawiła wyniku w praktycznym sensie względem pojedynczego detektora (F1: "
                "pedestrians −0.020, fountain01 +0.001)", l_pilot_v11),
    Claim("L4", "MOG2 połączony z kierunkowo spójnym ruchem poprawił F1 na obu sekwencjach, lecz był ok. 5–6× wolniejszy od MOG2", l_vector),
    Claim("L4b", "(czasy zależą od maszyny; w powtórce audytu 4.5–5.5×)",
          lambda: l_rerun_ratio_v11(["pedestrians", "fountain01"], 4.5, 5.5)),
    Claim("L5", "Sprawdzenie bez zmian progów na dwóch nowych sekwencjach", l_same_thresholds),
    Claim("L6", "F1 rośnie na `highway` i `canoe`, ale metoda nadal jest 3.8–4.0× wolniejsza od MOG2", l_independent),
    Claim("L6b", "(w powtórce audytu 4.0–4.6×)", lambda: l_rerun_ratio_v11(["highway", "canoe"], 4.0, 4.6)),
    Claim("L9", "F1 wszystkich raportów CDnet odtwarza się co do 4 miejsc przy ponownym uruchomieniu na surowych klatkach",
          l_all_reports_v11),
    Claim("L7", "przeliczanie pola co 2 klatki zachowuje prawie cały F1 pełnej fuzji przy około 1.6× krótszym czasie; rzadki "
                "LK w ROI wyraźnie traci recall", l_roi),
    Claim("V1", "medianą i 90. percentylem jego długości", v_p90),
    Claim("V2", "Na pierwszych 60% zdrowych par kalibruje medianę/MAD, a na pozostałych 40% próg kontrolny", v_split),
    Claim("T1", "45 testów, w tym 22 w `tests/test_i2d_core.py`: import każdego modułu", t_45_v11),
    Claim("T5", "pozostałe 23 dotyczą podobieństwa, CDnet, fuzji/diagnostyki, nakładek stereo i zdrowej referencji", t_23_v11),
    Claim("T2", "11 testów dla META_DYNAMICS v0.1/v0.2 (`test_meta_dynamics_v1.py` — kontrole syntetyczne k=3.5 i k=2.0", t_11),
    Claim("T3", "7 testów dla CONTOUR_CURVATURE v0.1", t_7),
    Claim("T4", "(N=4, za mało na sensowną regresję automatyczną)", t_n4),
]
ANCHORS = [("PREREG_META_DYNAMICS_v0.1.md", "RESULT_META_DYNAMICS_v0.1.md"),
           ("PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md", "RESULT_META_DYNAMICS_v0.2.md"),
           ("PREREG_META_DYNAMICS_v0.2.md", "RESULT_META_DYNAMICS_v0.2.md"),
           ("PREREG_CONTOUR_CURVATURE_v0.1.md", "RESULT_CONTOUR_CURVATURE_v0.1.md")]
ANCHOR_DISCLOSURE = r"Pre-rejestracje META_DYNAMICS i CONTOUR_CURVATURE trafiły do gita w tych samych commitach"
COMPLETENESS = [("RESULT_META_DYNAMICS_v0.2.md", r"NOT\s+SUPPORTED", r"NOT SUPPORTED", "RESULT v0.2: ρ NOT SUPPORTED"),
                ("RESULT_CONTOUR_CURVATURE_v0.1.md", r"CZĘŚCIOWO", r"CZĘŚCIOWO", "RESULT CONTOUR: częściowo")]
FORBIDDEN = [(r"wykrywa\w*\s+(manipulacj|anomali|splicing)\w*", r"\bnie\b|NIE", "gałęzie eksperymentalne nie są zwalidowanymi detektorami")]
ABSOLUTE = [(r"\btak samo\b", "podaj różnicę"), (r"\bzawsze\b|\bnigdy\b", "słowo bezwzględne"),
            (r"(?<!nie )\bdowodzi\b|\budowodni\w*", "„dowodzi” wymaga dowodu"), (r"(?<!\d)100 ?%", "sprawdź liczność")]
