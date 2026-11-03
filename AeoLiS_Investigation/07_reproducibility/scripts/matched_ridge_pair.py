"""Prepare or analyze the 128 x 64 reference-height-matched pilot."""
import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from prepare_ridge_cfd import prepare

N = 128
RESULTS = Path(__file__).resolve().parents[1] / "results"


def vectors(path, field):
    data = path.read_text().split(field, 1)[1]
    block = re.search(r"nonuniform\s+List<vector>\s+\d+\s*\(\s*\n(.*?)\n\)", data, re.S)[1]
    return np.fromstring(block.replace("(", "").replace(")", ""), sep=" ").reshape(-1, 3)


def wind(flat, coords, t):
    z = vectors(coords, "internalField")[:, 2].round(5)
    u = vectors(flat / str(t) / "U", "internalField")[:, 0]
    levels = np.unique(z)
    assert levels[0] < 10 < levels[-1] and len(levels) == 64
    return np.interp(10, levels, [u[z == level].mean() for level in levels])


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("mode", choices=["prepare", "analyze"])
parser.add_argument("pilot", type=Path)
parser.add_argument("work", type=Path)
args = parser.parse_args()
coords = args.pilot / "3000/C"
original = wind(args.pilot, coords, 3000)
bulk = 100 / original
print("Original U10 and calibrated bulk speed (m/s)", original, bulk)
cases = [(args.work/name, ratio) for name, ratio in [("flat", 0), ("gentle", .02), ("steep", .04)]]
if args.mode == "prepare":
    for case, ratio in cases:
        prepare(case, 32*ratio, N)
        forcing = case/"constant/fvOptions"
        forcing.write_text(forcing.read_text().replace("Ubar (10 ", f"Ubar ({bulk:.10f} "))
else:
    for case, _ in cases:
        if "Mesh OK." not in (case/"log.check").read_text():
            raise ValueError(f"Mesh check failed in {case}")
    flat = cases[0][0]
    speed = wind(flat, coords, 3000)
    print("Measured matched U10 (m/s)", speed)
    assert abs(speed - 10) <= .05
    aeolis = np.genfromtxt(RESULTS/"ridge_pair_full.csv", delimiter=",", names=True)
    fig, axes = plt.subplots(1, 2, sharey=True, figsize=(9,4), layout="constrained")
    rows = []
    for (case, ratio), ax in zip(cases[1:], axes):
        def profile(t):
            def wall(p):
                return vectors(p/str(t)/"wallShearStress", "    bed")[:,0]
            return wall(case)/wall(flat).mean()
        tau = profile(3000)
        x = (np.arange(N)+.5)/N-.5
        model = aeolis[aeolis["H_over_lambda"] == ratio]
        aligned = np.interp(x, model["x_over_lambda"], model["full_normalized"])
        print(ratio, "CFD min/max, peak x m, full AeoLiS peak, profile RMSE, iteration drift",
              tau.min(),tau.max(),32*x[tau.argmax()], model["full_normalized"].max(),
              np.sqrt(np.mean((aligned-tau)**2)),max(abs(tau-profile(2750))))
        rows.extend(zip(np.full(N,ratio),x,tau,aligned))
        ax.plot(x,tau,label="CFD")
        ax.plot(model["x_over_lambda"],model["full_normalized"],"--",label="Full AeoLiS")
        ax.set(title=f"H/λ = {ratio}",xlabel="Crest-relative distance / wavelength")
    axes[0].set_ylabel("Signed streamwise stress / flat-bed stress")
    axes[0].legend()
    fig.savefig(RESULTS/"matched_ridge_pair.png",dpi=200)
    np.savetxt(RESULTS/"matched_ridge_pair.csv",rows,delimiter=",",header="H_over_lambda,x_over_lambda,cfd_normalized,aeolis_interpolated",comments="")
