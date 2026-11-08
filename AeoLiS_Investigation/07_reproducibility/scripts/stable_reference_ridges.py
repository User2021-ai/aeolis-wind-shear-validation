"""Rerun both ridges with settled flat-bed forcing and normalization."""
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
from prepare_ridge_cfd import prepare
from ridge_grid_study import wall

RESULTS = Path(__file__).resolve().parents[1] / "results"
GRIDS = (64, 128, 256)
RIDGES = (("gentle", .02), ("steep", .04))


def generate(previous, references, output):
    for n in GRIDS:
        reference = references / f"flat-{n}"
        calibration = json.loads((reference / "calibration.json").read_text())
        target = calibration["new_bulk"]
        for name, ratio in RIDGES:
            source = previous / f"{name}-{n}"
            case = output / f"{name}-{n}"
            if case.exists():
                raise FileExistsError(case)
            prepare(case, 32 * ratio, n)
            old_bulk = float(re.search(r"Ubar \((\S+)", (source / "constant/fvOptions").read_text())[1])
            scale = target / old_bulk
            # Warm-start from the previous terrain solution at the same resolution.
            # Velocity scaling preserves the bulk target and dimensional consistency.
            for field, exponent in (("U", 1), ("p", 2), ("k", 2), ("epsilon", 3), ("nut", 1)):
                values = internal(source / f"9000/{field}") * scale**exponent
                assert len(values) == n * (n // 2)
                lines = ["(" + " ".join(map(str, row)) + ")" if field == "U" else str(row[0])
                         for row in values]
                replacement = (f"internalField nonuniform List<{'vector' if field == 'U' else 'scalar'}>\n"
                               f"{len(values)}\n(\n" + "\n".join(lines) + "\n);")
                path = case / f"0/{field}"
                path.write_text(re.sub(r"internalField uniform [^;]+;", replacement, path.read_text()))
            shutil.copyfile(reference / "constant/fvOptions", case / "constant/fvOptions")
            control = case / "system/controlDict"
            control.write_text(control.read_text().replace("endTime 3000", "endTime 6000")
                               .replace("writeInterval 250", "writeInterval 1000"))
            (case / "initialization.json").write_text(json.dumps(dict(previous_iteration=9000,
                velocity_scale=scale, bulk_target=target, height_to_wavelength=ratio), indent=2))


def analyze(work, flat_checks, time):
    aeolis = np.genfromtxt(RESULTS / "ridge_pair_full.csv", delimiter=",", names=True)
    records, rows, profiles = [], [], {}
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    history_figure, history_axes = plt.subplots(1, 2, figsize=(9, 3.5), layout="constrained")
    for n in GRIDS:
        denominator = wall(flat_checks / f"flat-{n}", 1000).mean()
        for col, (name, ratio) in enumerate(RIDGES):
            case = work / f"{name}-{n}"
            final_time = time or max(int(path.name) for path in case.iterdir() if path.is_dir() and path.name.isdigit())
            assert "Mesh OK." in (case / "log.check").read_text()
            logfile = "log.solve" if final_time == 6000 else f"log.to-{final_time}"
            assert "End" in (case / logfile).read_text()[-100:]
            tau = wall(case, final_time) / denominator
            assert len(tau) == n and np.isfinite(tau).all()
            x = (np.arange(n) + .5) / n - .5
            model = aeolis[aeolis["H_over_lambda"] == ratio]
            aligned = np.interp(x, model["x_over_lambda"], model["full_normalized"])
            changes = [float(max(abs(wall(case, t) - wall(case, t-1000))) / abs(denominator))
                       for t in (final_time-1000, final_time)]
            record = dict(nx=n, additional_iterations=final_time, height_to_wavelength=ratio, minimum=float(tau.min()),
                          peak=float(tau.max()), peak_x_m=float(32*x[tau.argmax()]),
                          rmse=float(np.sqrt(np.mean((aligned-tau)**2))),
                          last_two_window_max_changes=changes, stable=all(v < .002 for v in changes),
                          reversed_cell_count=int(sum(tau < 0)))
            record["initialization"] = json.loads((case / "initialization.json").read_text())
            history = []
            for checkpoint in range(2000, final_time+1, 1000):
                delta = float(max(abs(wall(case, checkpoint)-wall(case, checkpoint-1000))) / abs(denominator))
                history.append(dict(additional_iteration=checkpoint, max_normalized_change=delta))
            record["window_history"] = history
            files = [path for folder in ("0", "system", "constant")
                     for path in (case / folder).glob("*") if path.is_file()]
            record["input_sha256"] = {str(path.relative_to(case)): hashlib.sha256(path.read_bytes()).hexdigest()
                                      for path in files}
            records.append(record)
            profiles[n, ratio] = (x, tau)
            rows.extend(zip(np.full(n, n), np.full(n, ratio), x, tau, aligned))
            print(json.dumps({key: value for key, value in record.items() if key != "input_sha256"}))
            label = f"CFD {n} × {n//2}" + (" (still changing)" if not record["stable"] else "")
            axes[0, col].plot(x, tau, label=label)
            axes[1, col].plot(x, aligned-tau, label=f"Grid {n}")
            history_axes[col].semilogy([entry["additional_iteration"] for entry in history],
                                      [max(entry["max_normalized_change"], 1e-15) for entry in history],
                                      label=f"Grid {n}")
            archive = RESULTS / "stable_reference_ridge_logs" / case.name
            archive.mkdir(parents=True, exist_ok=True)
            filenames = ["log.check", "log.solve"] + [path.name for path in sorted(case.glob("log.to-*"))]
            for filename in filenames:
                (archive / (filename + ".gz")).write_bytes(gzip.compress((case / filename).read_bytes(), mtime=0))
    grid_changes = []
    for col, (_, ratio) in enumerate(RIDGES):
        model = aeolis[aeolis["H_over_lambda"] == ratio]
        axes[0, col].plot(model["x_over_lambda"], model["full_normalized"], "k--", label="AeoLiS full")
        axes[0, col].set_title(f"H/λ = {ratio}")
        history_axes[col].set(title=f"H/λ = {ratio}", xlabel="Additional iterations after restart",
                              ylabel="Maximum normalized stress change / 1,000 iterations")
        history_axes[col].axhline(.002, color=".5", ls="--", label="Proposed tolerance")
        history_axes[col].legend(fontsize=8)
        for coarse, fine in ((64,128), (128,256)):
            xc, tc = profiles[coarse, ratio]
            xf, tf = profiles[fine, ratio]
            mask = (xf >= xc.min()) & (xf <= xc.max())
            error = tf[mask] - np.interp(xf[mask], xc, tc)
            grid_changes.append(dict(height_to_wavelength=ratio, coarse=coarse, fine=fine,
                                     rms_change=float(np.sqrt(np.mean(error**2))),
                                     max_change=float(max(abs(error)))))
    for ax in axes.flat:
        ax.set_xlabel("Crest-relative distance / wavelength")
        ax.legend(fontsize=8)
    axes[0, 0].set_ylabel("Streamwise stress / settled flat-bed stress")
    axes[1, 0].set_ylabel("AeoLiS − CFD")
    fig.savefig(RESULTS / "stable_reference_ridges.png", dpi=200)
    history_figure.savefig(RESULTS / "stable_reference_ridge_convergence.png", dpi=200)
    (RESULTS / "stable_reference_ridges.json").write_text(json.dumps(dict(analysis_time_selection=time or "latest",
        records=records, grid_changes=grid_changes), indent=2) + "\n")
    np.savetxt(RESULTS / "stable_reference_ridges.csv", rows, delimiter=",",
               header="nx,H_over_lambda,x_over_lambda,cfd_normalized,aeolis_interpolated", comments="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "analyze"])
    parser.add_argument("work", type=Path)
    parser.add_argument("--previous", type=Path, default=Path("tmp/ridge-grid-study"))
    parser.add_argument("--references", type=Path, default=Path("tmp/flat-stability"))
    parser.add_argument("--flat-checks", type=Path, default=Path("tmp/flat-equilibrium-check"))
    parser.add_argument("--time", type=int, default=6000)
    args = parser.parse_args()
    if args.mode == "prepare":
        generate(args.previous, args.references, args.work)
    else:
        analyze(args.work, args.flat_checks, args.time)
