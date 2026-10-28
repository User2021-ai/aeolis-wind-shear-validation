"""Characterize B01 without modifying AeoLiS. Exit 1 if audited behavior changes."""

import argparse
import hashlib
import inspect
import json
import platform
import traceback
from pathlib import Path

import numpy as np
import scipy
from aeolis.shear import WindShear


def evaluate(z0):
    x, y = np.meshgrid(np.arange(64, dtype=float), np.arange(64, dtype=float))
    bed = 0.5 * np.cos(2 * np.pi * x / 16)
    model = WindShear(x, y, bed, dx=1., dy=1., L=100., l=10.,
                      z0=z0, buffer_width=10.)
    model.igrid = {"x": x, "y": y, "z": bed}
    model.cgrid.update(x=x, y=y, z=bed.copy())
    model.x0, model.y0 = float(x.mean()), float(y.mean())
    model.compute_shear(u0=10., nfilter=None)
    return model.cgrid["dtaux"], model.cgrid["dtauy"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    x = np.broadcast_to(np.arange(64, dtype=float), (64, 64))
    cases = {}
    for name, z0 in (
        ("scalar", 0.001),
        ("uniform_array", np.full((64, 64), 0.001)),
        ("variable_array", 0.001 * (1 + 0.25 * np.cos(2 * np.pi * x / 16))),
    ):
        try:
            tx, ty = evaluate(z0)
            cases[name] = {
                "status": "finite" if np.isfinite(tx).all() and np.isfinite(ty).all() else "nonfinite",
                "along_wind_rms": float(np.sqrt(np.mean(tx**2))),
                "transverse_rms": float(np.sqrt(np.mean(ty**2))),
            }
        except Exception as exc:
            frames = traceback.extract_tb(exc.__traceback__)
            cases[name] = {
                "status": "exception", "type": type(exc).__name__,
                "message": str(exc).strip(),
                "location": [
                    {"file": Path(f.filename).name, "line": f.lineno,
                     "function": f.name, "statement": f.line}
                    for f in frames if Path(f.filename).name == "shear.py"
                ],
            }
    reproduced = cases["scalar"]["status"] == "finite" and all(
        cases[name].get("type") == "ValueError"
        and "(4032,) (64,64)" in cases[name].get("message", "")
        and any(frame["function"] == "compute_shear" for frame in cases[name].get("location", []))
        for name in ("uniform_array", "variable_array")
    )
    source = Path(inspect.getfile(WindShear))
    report = {
        "scope": "Direct unfiltered FFT operator; no full time integration or CFD validation",
        "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
        "shear_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "cases": cases, "audited_failure_reproduced": bool(reproduced),
        "exit_code_meaning": "Zero confirms the known failure was reproduced; it does not mean B01 is fixed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if reproduced else 1)


if __name__ == "__main__":
    main()
