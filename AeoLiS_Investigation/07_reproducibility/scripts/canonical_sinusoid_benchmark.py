"""Verify AeoLiS's FFT shear operator for a periodic sinusoidal ridge.

This benchmark compares the numerical fundamental harmonic returned by
``WindShear.compute_shear`` with the analytical Fourier transfer coefficient
implemented by that same routine.  It is a code-verification experiment, not
an independent physical validation of the Weng parameterization.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "aeolis-matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import kv

from aeolis.shear import WindShear


KAPPA = 0.41


def analytical_transfer(
    wavelength: float, roughness: float, configured_length_scale: float
) -> complex:
    """Return the along-wind transfer coefficient used by AeoLiS.

    For ``h(x) = H cos(kx)``, the predicted shear perturbation is
    ``Re[T H exp(i k x)]``.  The internal factor ``L/4`` and the five fixed
    iterations reproduce ``WindShear.compute_shear`` exactly.
    """

    k = 2.0 * math.pi / wavelength
    internal_length = configured_length_scale / 4.0

    inner_height = 10.0
    for _ in range(5):
        inner_height = (
            2.0
            * KAPPA**2
            * internal_length
            / math.log(inner_height / roughness)
        )

    middle_height = 1.0
    for _ in range(5):
        middle_height = internal_length / math.sqrt(
            math.log(middle_height / roughness)
        )

    nondimensional_velocity = math.log(inner_height / roughness) / math.log(
        middle_height / roughness
    )
    sigma = np.sqrt(1j * internal_length * k * roughness / inner_height)
    term = -1.0 + (2.0 * math.log(inner_height / roughness) + 1.0) * sigma * (
        kv(1.0, 2.0 * sigma) / kv(0.0, 2.0 * sigma)
    )
    return complex(2.0 * k * term / nondimensional_velocity**2)


def numerical_operator(
    height: float,
    wavelength: float,
    points_per_wavelength: int,
    roughness: float,
    configured_length_scale: float,
    domain_wavelengths: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate the unfiltered AeoLiS FFT operator on an exact periodic mode."""

    dx = wavelength / points_per_wavelength
    nx = domain_wavelengths * points_per_wavelength
    ny = 8
    x_1d = np.arange(nx, dtype=float) * dx
    y_1d = np.arange(ny, dtype=float) * dx
    x, y = np.meshgrid(x_1d, y_1d)
    bed = height * np.cos(2.0 * math.pi * x / wavelength)

    model = WindShear(
        x,
        y,
        bed,
        dx=dx,
        dy=dx,
        L=configured_length_scale,
        l=10.0,
        z0=roughness,
        buffer_width=10.0,
    )
    model.igrid = {"x": x, "y": y, "z": bed}
    model.cgrid.update({"x": x, "y": y, "z": bed.copy()})
    model.x0, model.y0 = float(np.mean(x)), float(np.mean(y))
    model.compute_shear(u0=10.0, nfilter=None)
    return x_1d, bed[0], model.cgrid["dtaux"][0], model.cgrid["dtauy"][0]


def fit_harmonic(x: np.ndarray, values: np.ndarray, wavelength: float) -> dict:
    """Fit ``a cos(kx) + b sin(kx) + c`` and return amplitude and phase."""

    k = 2.0 * math.pi / wavelength
    design = np.column_stack((np.cos(k * x), np.sin(k * x), np.ones_like(x)))
    coefficients, *_ = np.linalg.lstsq(design, values, rcond=None)
    cosine, sine, offset = (float(value) for value in coefficients)
    fitted = design @ coefficients
    residual = values - fitted
    amplitude = math.hypot(cosine, sine)
    phase_radians = math.atan2(sine, cosine)
    return {
        "cosine_coefficient": cosine,
        "sine_coefficient": sine,
        "offset": offset,
        "amplitude": amplitude,
        "phase_degrees": math.degrees(phase_radians),
        "crest_shift_fraction_of_wavelength": phase_radians / (2.0 * math.pi),
        "residual_rms": float(np.sqrt(np.mean(residual**2))),
    }


def run_case(
    height_to_wavelength: float,
    wavelength: float,
    points_per_wavelength: int,
    roughness: float,
    configured_length_scale: float,
) -> tuple[dict, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """Run and diagnose one periodic-ridge case."""

    height = height_to_wavelength * wavelength
    x, bed, dtaux, dtauy = numerical_operator(
        height,
        wavelength,
        points_per_wavelength,
        roughness,
        configured_length_scale,
    )
    fitted = fit_harmonic(x, dtaux, wavelength)
    transfer = analytical_transfer(wavelength, roughness, configured_length_scale)
    expected_amplitude = height * abs(transfer)
    expected_phase = -math.degrees(np.angle(transfer))
    amplitude_relative_error = abs(fitted["amplitude"] - expected_amplitude) / max(
        expected_amplitude, np.finfo(float).tiny
    )
    phase_error = abs(
        ((fitted["phase_degrees"] - expected_phase + 180.0) % 360.0) - 180.0
    )
    transverse_rms = float(np.sqrt(np.mean(dtauy**2)))

    record = {
        "height_to_wavelength": height_to_wavelength,
        "height_m": height,
        "maximum_slope": 2.0 * math.pi * height_to_wavelength,
        "maximum_slope_degrees": math.degrees(
            math.atan(2.0 * math.pi * height_to_wavelength)
        ),
        "points_per_wavelength": points_per_wavelength,
        "configured_length_scale_m": configured_length_scale,
        "roughness_m": roughness,
        "fitted": fitted,
        "normalized_gain_per_m": fitted["amplitude"] / height,
        "minimum_total_shear_for_unit_background": 1.0 - fitted["amplitude"],
        "would_require_nonnegative_shear_clip": bool(fitted["amplitude"] > 1.0),
        "expected_amplitude": expected_amplitude,
        "expected_phase_degrees": expected_phase,
        "amplitude_relative_error": amplitude_relative_error,
        "phase_absolute_error_degrees": phase_error,
        "transverse_rms": transverse_rms,
    }
    return record, (x, bed, dtaux)


def create_figure(results: dict, profile: tuple[np.ndarray, ...], path: Path) -> None:
    """Create a compact four-panel diagnostic figure."""

    path.parent.mkdir(parents=True, exist_ok=True)
    x, bed, dtaux = profile
    slope_cases = results["slope_sweep"]
    resolution_cases = results["resolution_sweep"]
    length_cases = results["length_scale_sweep"]

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8.0), constrained_layout=True)

    ax = axes[0, 0]
    ax.plot(x, bed / np.max(np.abs(bed)), label="bed elevation / H", lw=2)
    ax.plot(x, dtaux / np.max(np.abs(dtaux)), label="shear perturbation / max", lw=2)
    ax.set_xlim(0.0, 2.0 * results["configuration"]["wavelength_m"])
    ax.set_xlabel("x (m)")
    ax.set_ylabel("normalized value")
    ax.set_title("A. Baseline harmonic and phase lead")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)

    ax = axes[0, 1]
    slope_degrees = [case["maximum_slope_degrees"] for case in slope_cases]
    amplitudes = [case["fitted"]["amplitude"] for case in slope_cases]
    phases = [case["fitted"]["phase_degrees"] for case in slope_cases]
    ax.plot(slope_degrees, amplitudes, "o-", color="tab:blue", label="amplitude")
    ax.axhline(1.0, color="tab:red", ls=":", label="unit background stress")
    ax.set_xlabel("maximum bed-slope angle (degrees)")
    ax.set_ylabel("nondimensional perturbation amplitude", color="tab:blue")
    ax.tick_params(axis="y", labelcolor="tab:blue")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, loc="upper left")
    twin = ax.twinx()
    twin.plot(slope_degrees, phases, "s--", color="tab:orange", label="phase")
    twin.set_ylabel("shear-maximum shift (degrees)", color="tab:orange")
    twin.tick_params(axis="y", labelcolor="tab:orange")
    ax.set_title("B. Linear response across amplitude")

    ax = axes[1, 0]
    ppw = [case["points_per_wavelength"] for case in resolution_cases]
    amp_error = [max(case["amplitude_relative_error"], 1e-18) for case in resolution_cases]
    phase_error = [
        max(case["phase_absolute_error_degrees"], 1e-16)
        for case in resolution_cases
    ]
    ax.loglog(ppw, amp_error, "o-", label="amplitude relative error")
    ax.loglog(ppw, phase_error, "s--", label="phase error (degrees)")
    ax.set_xlabel("points per wavelength")
    ax.set_ylabel("error against implemented transfer")
    ax.set_title("C. Exact-mode numerical verification")
    ax.grid(alpha=0.25, which="both")
    ax.legend(frameon=False)

    ax = axes[1, 1]
    scales = [case["configured_length_scale_m"] for case in length_cases]
    length_gains = [case["normalized_gain_per_m"] for case in length_cases]
    length_phases = [case["fitted"]["phase_degrees"] for case in length_cases]
    ax.semilogx(scales, length_gains, "o-", color="tab:blue")
    ax.set_xlabel("configured L (m)")
    ax.set_ylabel("amplitude / H (m$^{-1}$)", color="tab:blue")
    ax.tick_params(axis="y", labelcolor="tab:blue")
    ax.grid(alpha=0.25)
    twin = ax.twinx()
    twin.semilogx(scales, length_phases, "s--", color="tab:orange")
    twin.set_ylabel("phase shift (degrees)", color="tab:orange")
    twin.tick_params(axis="y", labelcolor="tab:orange")
    ax.set_title("D. Sensitivity to single configured L")

    fig.suptitle("AeoLiS canonical sinusoidal-ridge verification", fontsize=14)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_benchmark() -> tuple[dict, tuple[np.ndarray, ...]]:
    """Run slope, resolution, and length-scale sweeps."""

    wavelength = 32.0
    roughness = 1.0e-3
    baseline_ratio = 0.02
    baseline_ppw = 32
    baseline_length = 100.0

    slope_sweep = []
    baseline_profile = None
    for ratio in (0.0025, 0.005, 0.01, 0.02, 0.04):
        case, profile = run_case(
            ratio, wavelength, baseline_ppw, roughness, baseline_length
        )
        slope_sweep.append(case)
        if ratio == baseline_ratio:
            baseline_profile = profile

    resolution_sweep = [
        run_case(baseline_ratio, wavelength, ppw, roughness, baseline_length)[0]
        for ppw in (8, 12, 16, 24, 32, 48, 64)
    ]
    length_scale_sweep = [
        run_case(baseline_ratio, wavelength, baseline_ppw, roughness, length)[0]
        for length in (25.0, 50.0, 100.0, 200.0, 400.0)
    ]
    wavelength_sweep = [
        run_case(baseline_ratio, value, baseline_ppw, roughness, baseline_length)[0]
        for value in (16.0, 24.0, 32.0, 48.0, 64.0)
    ]
    roughness_sweep = [
        run_case(baseline_ratio, wavelength, baseline_ppw, value, baseline_length)[0]
        for value in (1.0e-5, 1.0e-4, 1.0e-3, 1.0e-2)
    ]

    all_cases = (
        slope_sweep
        + resolution_sweep
        + length_scale_sweep
        + wavelength_sweep
        + roughness_sweep
    )
    max_amplitude_error = max(
        case["amplitude_relative_error"] for case in all_cases
    )
    max_phase_error = max(
        case["phase_absolute_error_degrees"] for case in all_cases
    )
    max_transverse_rms = max(case["transverse_rms"] for case in all_cases)
    normalized_gains = [case["normalized_gain_per_m"] for case in slope_sweep]
    gain_spread = (max(normalized_gains) - min(normalized_gains)) / np.mean(
        normalized_gains
    )

    results = {
        "benchmark": "A01 canonical periodic sinusoidal ridge",
        "classification": "implementation verification, not physical validation",
        "configuration": {
            "wavelength_m": wavelength,
            "roughness_m": roughness,
            "baseline_height_to_wavelength": baseline_ratio,
            "baseline_points_per_wavelength": baseline_ppw,
            "baseline_configured_length_scale_m": baseline_length,
            "wind_direction": "positive x",
            "high_frequency_filter": None,
        },
        "slope_sweep": slope_sweep,
        "resolution_sweep": resolution_sweep,
        "length_scale_sweep": length_scale_sweep,
        "wavelength_sweep": wavelength_sweep,
        "roughness_sweep": roughness_sweep,
        "verification_summary": {
            "number_of_cases": len(all_cases),
            "maximum_amplitude_relative_error": max_amplitude_error,
            "maximum_phase_absolute_error_degrees": max_phase_error,
            "maximum_transverse_rms": max_transverse_rms,
            "relative_gain_spread_across_amplitudes": float(gain_spread),
            "first_slope_case_requiring_nonnegative_clip": next(
                (
                    case["height_to_wavelength"]
                    for case in slope_sweep
                    if case["would_require_nonnegative_shear_clip"]
                ),
                None,
            ),
            "pass": bool(
                max_amplitude_error < 1.0e-10
                and max_phase_error < 1.0e-10
                and max_transverse_rms < 1.0e-12
                and gain_spread < 1.0e-10
            ),
        },
        "interpretation": [
            "The exact periodic Fourier mode should match the implemented transfer coefficient to floating-point precision.",
            "Amplitude-independent normalized gain confirms that this operator is linear; it does not establish validity for steep or separated dunes.",
            "Sensitivity to configured L is a model/configuration sensitivity, not numerical grid error.",
            "Once perturbation amplitude exceeds the unit background stress, the linear result predicts negative lee-side stress and the full model must clip or otherwise correct it.",
            "An exact periodic Fourier mode cannot expose boundary leakage or ordinary discretization error; a non-periodic benchmark is required next.",
            "CFD and field comparisons are still required for physical validation.",
        ],
    }
    assert baseline_profile is not None
    return results, baseline_profile


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    args = parser.parse_args()

    results, profile = run_benchmark()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    create_figure(results, profile, args.figure)
    print(json.dumps(results["verification_summary"], indent=2))
    print(args.output)
    print(args.figure)


if __name__ == "__main__":
    main()
