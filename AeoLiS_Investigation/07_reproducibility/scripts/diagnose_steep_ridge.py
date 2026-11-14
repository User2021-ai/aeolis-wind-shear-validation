"""Compare numerical controls from a common fine steep-ridge restart."""
import argparse
import gzip
import hashlib
import json
import re
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from flat_reference_stability import internal
from ridge_grid_study import wall

RESULTS = Path(__file__).resolve().parents[1] / "results"
VARIANTS = ("control", "tight", "relaxed")


def prepare(source, work):
    for name in VARIANTS:
        case = work / name
        if case.exists():
            raise FileExistsError(case)
        case.mkdir(parents=True)
        for part in ("system", "constant", "12000"):
            shutil.copytree(source / part, case / part)
        control = case / "system/controlDict"
        control.write_text(control.read_text().replace("endTime 12000", "endTime 16000"))
        solution = case / "system/fvSolution"
        text = solution.read_text()
        if name == "tight":
            text = text.replace("tolerance 1e-9; relTol 0.01;", "tolerance 1e-10; relTol 0;")
        elif name == "relaxed":
            text = text.replace("p 0.3;", "p 0.2;").replace("U 0.7; k 0.6; epsilon 0.6;",
                                                                    "U 0.4; k 0.3; epsilon 0.3;")
        solution.write_text(text)


def snapshot(case, time, reference, volumes):
    folder = case / str(time)
    stress = wall(case, time) / reference
    velocity = internal(folder / "U")
    kinetic = internal(folder / "k")[:, 0]
    epsilon = internal(folder / "epsilon")[:, 0]
    for values in (stress, velocity, kinetic, epsilon):
        assert np.isfinite(values).all()
    gradient_text = (folder / "uniform/driveProperties").read_text()
    gradient = float(re.search(r"\bgradient\s+([^;]+)", gradient_text)[1])
    return dict(time=time, minimum=float(stress.min()), peak=float(stress.max()),
                bulk_ux=float(np.average(velocity[:, 0], weights=volumes)),
                maximum_speed=float(np.linalg.norm(velocity, axis=1).max()),
                minimum_k=float(kinetic.min()), maximum_k=float(kinetic.max()),
                minimum_epsilon=float(epsilon.min()), maximum_epsilon=float(epsilon.max()),
                pressure_gradient=gradient), stress


def analyze(source, work, flat):
    reference = wall(flat, 1000).mean()
    volumes = internal(work / "control/12000/V")[:, 0]
    assert (volumes > 0).all()
    original = []
    for time in range(1000, 12001, 1000):
        row, _ = snapshot(source, time, reference, volumes)
        original.append(row)
    records = {}
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    for name in VARIANTS:
        case = work / name
        assert "End" in (case / "log.solve").read_text()[-100:]
        hashes = {}
        for field in ("U", "p", "k", "epsilon", "nut", "phi"):
            restart = case / f"12000/{field}"
            expected = source / f"12000/{field}"
            digest = hashlib.sha256(restart.read_bytes()).hexdigest()
            assert digest == hashlib.sha256(expected.read_bytes()).hexdigest()
            hashes[field] = digest
        history = []
        previous = wall(case, 12000) / reference
        for time in range(13000, 16001, 1000):
            row, stress = snapshot(case, time, reference, volumes)
            delta = stress - previous
            row["max_normalized_stress_change"] = float(max(abs(delta)))
            row["x_of_max_change_m"] = float(-16+(np.argmax(abs(delta))+.5)*32/256)
            history.append(row)
            previous = stress
        last_changes = [row["max_normalized_stress_change"] for row in history[-2:]]
        record = dict(history=history, passes_window_test=all(value < .002 for value in last_changes),
                      restart_field_sha256=hashes)
        baseline = wall(work / "control", 16000) / reference
        record["final_rms_stress_difference_from_control"] = float(np.sqrt(np.mean((stress-baseline)**2)))
        for field in ("U", "k", "epsilon"):
            start = internal(case / f"15000/{field}")
            end = internal(case / f"16000/{field}")
            record[f"last_window_max_{field}_change"] = float(max(abs(end-start).ravel()))
        records[name] = record
        x = (np.arange(256)+.5)/256-.5
        axes[0, 0].plot(x, stress, label=name)
        axes[0, 1].plot([row["time"] for row in history],
                        [row["max_normalized_stress_change"] for row in history], label=name)
        axes[1, 0].plot([row["time"] for row in history], [row["pressure_gradient"] for row in history], label=name)
        axes[1, 1].plot([row["time"] for row in history], [row["maximum_k"] for row in history], label=name)
        archive = RESULTS / "steep_ridge_diagnostic_logs" / name
        archive.mkdir(parents=True, exist_ok=True)
        (archive / "log.solve.gz").write_bytes(gzip.compress((case / "log.solve").read_bytes(), mtime=0))
        shutil.copyfile(case / "system/fvSolution", archive / "fvSolution")
        print(name, json.dumps(record))
    axes[0, 0].set(xlabel="Crest-relative distance / wavelength", ylabel="Stress / settled flat-bed stress")
    axes[0, 1].axhline(.002, color=".5", ls="--", label="Proposed tolerance")
    axes[0, 1].set(xlabel="Restart iteration index", ylabel="Maximum stress change / 1,000 iterations")
    axes[1, 0].set(xlabel="Restart iteration index", ylabel="Driving acceleration (m/s²)")
    axes[1, 1].set(xlabel="Restart iteration index", ylabel="Maximum turbulent kinetic energy (m²/s²)")
    for ax in axes.flat:
        ax.legend(fontsize=8)
    fig.savefig(RESULTS / "steep_ridge_diagnosis.png", dpi=200)
    profiles = [(np.arange(256)+.5)/256-.5]
    profiles.extend(wall(work / name, 16000)/reference for name in VARIANTS)
    np.savetxt(RESULTS / "steep_ridge_diagnostic_profiles.csv", np.column_stack(profiles), delimiter=",",
               header="x_over_wavelength,control_normalized,tight_normalized,relaxed_normalized", comments="")
    (RESULTS / "steep_ridge_diagnosis.json").write_text(json.dumps(dict(original_history=original,
                                                                            variants=records), indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "analyze"])
    parser.add_argument("work", type=Path)
    parser.add_argument("--source", type=Path, default=Path("tmp/stable-reference-ridges/steep-256"))
    parser.add_argument("--flat", type=Path, default=Path("tmp/flat-equilibrium-check/flat-256"))
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.source, args.work)
    else:
        analyze(args.source, args.work, args.flat)
