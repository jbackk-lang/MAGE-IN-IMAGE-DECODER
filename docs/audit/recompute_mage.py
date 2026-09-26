"""Przeliczenia dla audytu twierdzeń README (MAGE-IN-IMAGE-DECODER). Reguły: docs/audit/CLAIM_AUDIT_PREREG.md.

Tryby (katalog repo):
  python docs/audit/recompute_mage.py local            # skrypty META/kalibracja/CONTOUR, testy, kod -> RECOMPUTE_MAGE.json
  python docs/audit/recompute_mage.py cdnet OUT.json    # dopisuje wynik ponownego uruchomienia cdnet_benchmark (OUT.json)
CDnet uruchamiany osobno: python cdnet_benchmark.py <4 sekwencje> --output OUT.json
"""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "RECOMPUTE_MAGE.json"
sys.path.insert(0, str(REPO))


def save(key, value):
    d = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    d[key] = value
    OUT.write_text(json.dumps(d, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def collect(paths):
    p = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q", *paths],
                       cwd=REPO, capture_output=True, text=True, timeout=150)
    return sum("::" in l for l in p.stdout.splitlines())


def run_local():
    out = {}
    import real_meta_dynamics_ped2 as rm
    with contextlib.redirect_stdout(io.StringIO()):
        r = rm.run_real_test(verbose=False)
    out["meta_real"] = json.loads(json.dumps(r, default=float))
    out["meta_real_alpha"] = float(getattr(rm, "ALPHA_CORR"))
    import calibrate_rho_threshold as cr
    with contextlib.redirect_stdout(io.StringIO()):
        out["calibration"] = json.loads(json.dumps(cr.run_calibration(verbose=False), default=float))
    import real_contour_curvature_casia2 as rc
    with contextlib.redirect_stdout(io.StringIO()):
        res = rc.run_real_test(verbose=False)
    out["contour_real"] = [json.loads(json.dumps(getattr(x, "__dict__", x), default=float)) for x in res]
    tests = {"tests_dir": collect(["tests"]), "tests_i2d_core": collect(["tests/test_i2d_core.py"]),
             "meta": collect(["test_meta_dynamics_v1.py", "test_meta_dynamics_ped2_real.py"]),
             "contour": collect(["test_contour_curvature.py"])}
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "test_meta_dynamics_v1.py",
                        "test_meta_dynamics_ped2_real.py", "test_contour_curvature.py"], cwd=REPO, capture_output=True,
                       text=True, timeout=170)
    tests["run_tail"], tests["returncode"] = p.stdout.strip().splitlines()[-1:], p.returncode
    out["tests"] = tests
    cal = REPO / "data" / "ucsd_ped2_calibration" / "Test"
    tst = REPO / "data" / "ucsd_ped2" / "Test"
    out["dirs"] = {"calibration_clips": sorted(p.name for p in cal.iterdir() if p.is_dir()) if cal.exists() else [],
                   "test_clips": sorted(p.name for p in tst.iterdir() if p.is_dir()) if tst.exists() else [],
                   "casia_images": sorted(p.name for p in (REPO / "data" / "casia2_splicing_sample").glob("*.jpg"))}
    for k, v in out.items():
        save(k, v)


def run_cdnet(path):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    save("cdnet_rerun", d)


if __name__ == "__main__":
    if sys.argv[1] == "local":
        run_local()
    else:
        run_cdnet(sys.argv[2])
    print(OUT.read_text(encoding="utf-8")[:4000])
