"""Prepare and assess matched periodic ridge cases on three CFD grids."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from prepare_ridge_cfd import prepare

RESULTS = Path(__file__).resolve().parents[1] / "results"
GRIDS = (64, 128, 256)
CASES = (("flat", 0), ("gentle", .02), ("steep", .04))


def vectors(path, field):
    data = path.read_text().split(field, 1)[1]
    match = re.search(r"nonuniform\s+List<vector>\s+(\d+)\s*\(\s*\n(.*?)\n\)", data, re.S)
    values = np.fromstring(match[2].replace("(", "").replace(")", ""), sep=" ").reshape(-1, 3)
    assert len(values) == int(match[1]) and np.isfinite(values).all()
    return values


def u10(case, coords, time):
    heights = vectors(coords, "internalField")[:, 2].round(5)
    velocity = vectors(case / str(time) / "U", "internalField")[:, 0]
    levels = np.unique(heights)
    assert levels[0] < 10 < levels[-1] and len(heights) == len(velocity)
    return float(np.interp(10, levels, [velocity[heights == z].mean() for z in levels]))


def wall(case, time):
    return vectors(case / str(time) / "wallShearStress", "    bed")[:, 0]


def generate(pilot, work):
    for n in GRIDS:
        flat = pilot / f"flat-{n}"
        original = u10(flat, flat / "3000/C", 3000)
        for name, ratio in CASES:
            case = work / f"{name}-{n}"
            if case.exists():
                raise FileExistsError(f"Preserve existing results in {case}")
            prepare(case, 32 * ratio, n)
            control = case / "system/controlDict"
            control.write_text(control.read_text().replace("endTime 3000", "endTime 6000"))
            forcing = case / "constant/fvOptions"
            forcing.write_text(forcing.read_text().replace("Ubar (10 ", f"Ubar ({100/original:.10f} "))
        print(n, "pilot U10", original, "new bulk target", 100/original)


def recalibrate(pilot, work, grids):
    for n in grids:
        flat = work / f"flat-{n}"
        history = work / f"calibration-{n}.json"
        if history.exists():
            raise FileExistsError(f"Grid {n} has already been recalibrated")
        measured = u10(flat, pilot / f"flat-{n}/3000/C", 6000)
        for name, _ in CASES:
            case = work / f"{name}-{n}"
            forcing = case / "constant/fvOptions"
            text = forcing.read_text()
            bulk = float(re.search(r"Ubar \((\S+)", text)[1]) * 10 / measured
            forcing.write_text(re.sub(r"Ubar \(\S+", f"Ubar ({bulk:.10f}", text))
            control = case / "system/controlDict"
            control.write_text(control.read_text().replace("startFrom startTime", "startFrom latestTime")
                               .replace("endTime 6000", "endTime 9000"))
        print(n, "recalibrated using U10", measured, "bulk target", bulk)
        history.write_text(json.dumps(dict(u10_at_6000=measured, bulk_target=bulk), indent=2))


def analyze(pilot, work, time):
    aeolis = np.genfromtxt(RESULTS / "ridge_pair_full.csv", delimiter=",", names=True)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    records, rows = [], []
    evidence = {}
    profiles = {}
    for n in GRIDS:
        flat = work / f"flat-{n}"
        speed = u10(flat, pilot / f"flat-{n}/3000/C", time)
        for col, (name, ratio) in enumerate(CASES[1:]):
            case = work / f"{name}-{n}"
            for directory in (flat, case):
                assert "Mesh OK." in (directory / "log.check").read_text()
                log = "log.continue" if time > 6000 else "log.solve"
                assert "End" in (directory / log).read_text()[-100:]
                if directory.name not in evidence:
                    files = [p for folder in ("0", "system", "constant")
                             for p in (directory / folder).glob("*") if p.is_file()]
                    evidence[directory.name] = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                                                for p in files}
                    archive = RESULTS / "ridge_grid_logs" / directory.name
                    archive.mkdir(parents=True, exist_ok=True)
                    for filename in ("log.check", "log.solve", "log.continue"):
                        if not (directory / filename).exists():
                            continue
                        (archive / (filename + ".gz")).write_bytes(gzip.compress((directory / filename).read_bytes(), mtime=0))
            tau = wall(case, time) / wall(flat, time).mean()
            assert len(tau) == n
            x = (np.arange(n) + .5) / n - .5
            model = aeolis[aeolis["H_over_lambda"] == ratio]
            aligned = np.interp(x, model["x_over_lambda"], model["full_normalized"])
            change = max(abs(tau - wall(case, time-250) / wall(flat, time-250).mean()))
            long_change = max(abs(tau - wall(case, time-1000) / wall(flat, time-1000).mean()))
            record = dict(nx=n, height_to_wavelength=ratio, flat_u10_m_s=speed,
                          minimum=float(tau.min()), peak=float(tau.max()),
                          peak_x_m=float(32*x[tau.argmax()]), rmse=float(np.sqrt(np.mean((tau-aligned)**2))),
                          last_250_change=float(change), last_1000_change=float(long_change),
                          reversed_cell_count=int(sum(tau < 0)))
            records.append(record)
            profiles[n, ratio] = (x, tau)
            rows.extend(zip(np.full(n, n), np.full(n, ratio), x, tau, aligned))
            axes[0, col].plot(x, tau, label=f"CFD {n} × {n//2}")
            axes[1, col].plot(x, aligned-tau, label=f"Grid {n}")
            print(json.dumps(record))
    differences = []
    for col, (_, ratio) in enumerate(CASES[1:]):
        model = aeolis[aeolis["H_over_lambda"] == ratio]
        axes[0, col].plot(model["x_over_lambda"], model["full_normalized"], "k--", label="AeoLiS full")
        axes[0, col].set_title(f"H/λ = {ratio}")
        for coarse, fine in ((64,128), (128,256)):
            xc, tc = profiles[coarse, ratio]
            xf, tf = profiles[fine, ratio]
            # Restrict to the shared cell-centre extent, avoiding endpoint extrapolation.
            mask = (xf >= xc.min()) & (xf <= xc.max())
            error = tf[mask] - np.interp(xf[mask], xc, tc)
            differences.append(dict(height_to_wavelength=ratio, coarse=coarse, fine=fine,
                                    profile_rms_change=float(np.sqrt(np.mean(error**2))),
                                    profile_max_change=float(max(abs(error)))))
    for ax in axes.flat:
        ax.set_xlabel("Crest-relative distance / wavelength")
        ax.legend(fontsize=8)
    axes[0, 0].set_ylabel("Streamwise stress / flat-bed stress")
    axes[1, 0].set_ylabel("AeoLiS − CFD")
    fig.savefig(RESULTS / "ridge_grid_study.png", dpi=200)
    calibration = {str(n): json.loads((work / f"calibration-{n}.json").read_text()) for n in GRIDS}
    (RESULTS / "ridge_grid_study.json").write_text(json.dumps(dict(iterations=time, records=records,
                                                       grid_differences=differences, calibration=calibration,
                                                       input_sha256=evidence), indent=2)+"\n")
    np.savetxt(RESULTS / "ridge_grid_study.csv", rows, delimiter=",",
               header="nx,H_over_lambda,x_over_lambda,cfd_normalized,aeolis_interpolated", comments="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "recalibrate", "analyze"])
    parser.add_argument("pilot", type=Path)
    parser.add_argument("work", type=Path)
    parser.add_argument("--grids", nargs="+", type=int, choices=GRIDS, default=list(GRIDS))
    parser.add_argument("--time", type=int, default=9000)
    args = parser.parse_args()
    if args.mode == "prepare":
        generate(args.pilot, args.work)
    elif args.mode == "recalibrate":
        recalibrate(args.pilot, args.work, args.grids)
    else:
        analyze(args.pilot, args.work, args.time)
