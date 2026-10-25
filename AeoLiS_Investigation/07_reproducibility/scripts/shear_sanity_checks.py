"""Small, deterministic checks for the AeoLiS 3.1.0rc1 FFT shear operator.

Run from the aeolis-python repository root, or set PYTHONPATH to that checkout.
The script does not modify the model and writes a machine-readable JSON report.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from aeolis.shear import WindShear


def _operator(z: np.ndarray, dx: float, z0, length_scale: float = 100.0):
    ny, nx = z.shape
    x, y = np.meshgrid(np.arange(nx) * dx, np.arange(ny) * dx)
    model = WindShear(
        x,
        y,
        z,
        dx=dx,
        dy=dx,
        L=length_scale,
        l=10.0,
        z0=z0,
        buffer_width=10.0,
    )
    model.igrid = {"x": x, "y": y, "z": z}
    model.cgrid.update({"x": x, "y": y, "z": z.copy()})
    model.x0, model.y0 = float(np.mean(x)), float(np.mean(y))
    model.compute_shear(u0=10.0, nfilter=None)
    return model.cgrid["dtaux"], model.cgrid["dtauy"]


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a))))


def run_checks() -> dict:
    results: dict[str, object] = {
        "baseline": {
            "version": "AeoLiS 3.1.0rc1",
            "commit": "1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e",
        }
    }

    n = 64
    dx = 1.0
    x, y = np.meshgrid(np.arange(n) * dx, np.arange(n) * dx)

    flat_x, flat_y = _operator(np.zeros((n, n)), dx, 1.0e-3)
    results["flat_bed"] = {
        "max_abs_dtaux": float(np.max(np.abs(flat_x))),
        "max_abs_dtauy": float(np.max(np.abs(flat_y))),
        "pass": bool(np.allclose(flat_x, 0.0) and np.allclose(flat_y, 0.0)),
    }

    wavelength = 16.0
    ridge = 0.5 * np.cos(2.0 * np.pi * x / wavelength)
    ridge_x, ridge_y = _operator(ridge, dx, 1.0e-3)
    results["along_wind_ridge"] = {
        "rms_dtaux": _rms(ridge_x),
        "rms_dtauy": _rms(ridge_y),
        "transverse_ratio": _rms(ridge_y) / max(_rms(ridge_x), np.finfo(float).tiny),
        "pass": bool(np.all(np.isfinite(ridge_x)) and np.allclose(ridge_y, 0.0, atol=1e-12)),
    }

    crosswind_only = 0.5 * np.cos(2.0 * np.pi * y / wavelength)
    cross_x, cross_y = _operator(crosswind_only, dx, 1.0e-3)
    results["crosswind_only_topography"] = {
        "rms_dtaux": _rms(cross_x),
        "rms_dtauy": _rms(cross_y),
        "pass_under_linear_theory": bool(np.allclose(cross_x, 0.0) and np.allclose(cross_y, 0.0)),
        "interpretation": "Expected for the implemented along-wind linear perturbation theory; not a general CFD result.",
    }

    shifted_x, shifted_y = _operator(ridge + 37.0, dx, 1.0e-3)
    results["vertical_datum_invariance"] = {
        "max_abs_x_difference": float(np.max(np.abs(shifted_x - ridge_x))),
        "max_abs_y_difference": float(np.max(np.abs(shifted_y - ridge_y))),
        "pass": bool(np.allclose(shifted_x, ridge_x, atol=1e-12) and np.allclose(shifted_y, ridge_y, atol=1e-12)),
    }

    sensitivity = {}
    for length_scale in (25.0, 100.0, 400.0):
        sx, sy = _operator(ridge, dx, 1.0e-3, length_scale=length_scale)
        sensitivity[str(length_scale)] = {"rms_dtaux": _rms(sx), "rms_dtauy": _rms(sy)}
    values = [sensitivity[key]["rms_dtaux"] for key in ("25.0", "100.0", "400.0")]
    results["configured_length_scale_sensitivity"] = {
        "cases": sensitivity,
        "max_to_min_rms_ratio": float(max(values) / min(values)),
        "interpretation": "The legacy Weng implementation uses one configured L for every Fourier mode.",
    }

    variable_z0_error = None
    try:
        z0_field = 1.0e-3 * (1.0 + 0.25 * np.cos(2.0 * np.pi * x / wavelength))
        _operator(ridge, dx, z0_field)
    except Exception as exc:  # this check intentionally captures the current failure mode
        variable_z0_error = {"type": type(exc).__name__, "message": str(exc)}
    results["spatially_variable_roughness"] = {
        "exception": variable_z0_error,
        "pass": variable_z0_error is None,
        "interpretation": "Adaptive roughness returns an array; the FFT implementation mixes a 2-D inner-layer array with a 1-D Fourier mask.",
    }

    oblique = 0.5 * np.cos(2.0 * np.pi * (x + y) / (wavelength * math.sqrt(2.0)))
    oblique_x, oblique_y = _operator(oblique, dx, 1.0e-3)
    results["oblique_mode"] = {
        "finite": bool(np.all(np.isfinite(oblique_x)) and np.all(np.isfinite(oblique_y))),
        "rms_dtaux": _rms(oblique_x),
        "rms_dtauy": _rms(oblique_y),
    }

    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(run_checks(), indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
