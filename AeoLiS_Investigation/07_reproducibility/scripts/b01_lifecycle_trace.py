"""Exercise real wind lifecycle functions; not a full morphodynamic run."""

import argparse
import copy
import json
from pathlib import Path

import numpy as np
from aeolis import wind
from aeolis.constants import DEFAULT_CONFIG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    x, y = np.meshgrid(np.arange(16, dtype=float), np.arange(16, dtype=float))
    s = {"x": x, "y": y, "zb": 0.05 * np.cos(2 * np.pi * x / 16)}
    for key in ("uw", "udir", "taus", "taun", "ustars", "ustarn"):
        s[key] = np.zeros_like(x)
    p = copy.deepcopy(DEFAULT_CONFIG)
    p.update(process_shear=True, process_wind=True, process_separation=False,
             method_shear="fft", method_roughness="constant", k=0.001,
             ny=15, dx=1., dy=1., alfa=0.,
             wind_file=np.array([[0., 10., 260.], [1., 10., 260.]]))
    wind.initialize(s, p)
    wind.interpolate(s, p, 0.)
    initial_fft_z0 = float(s["shear"].z0)
    initial_ustar = float(s["ustar"][0, 0])
    # Controlled parameter change isolates update propagation without sediment physics.
    p["k"] = 0.002
    wind.interpolate(s, p, 1.)
    updated_ustar = float(s["ustar"][0, 0])
    updated_local_z0 = float(wind.calculate_z0(p, s))
    wind.shear(s, p)
    after_shear_z0 = float(s["shear"].z0)
    confirmed = bool(initial_fft_z0 == after_shear_z0 == 0.001
                     and updated_local_z0 == 0.002
                     and updated_ustar > initial_ustar
                     and np.isfinite(s["tau"]).all())
    result = {
        "scope": "Actual wind.initialize, wind.interpolate and wind.shear calls; controlled scalar change, no full model.update or sediment evolution",
        "initial_fft_z0_m": initial_fft_z0,
        "updated_log_law_z0_m": updated_local_z0,
        "fft_z0_after_shear_m": after_shear_z0,
        "initial_log_law_ustar": initial_ustar,
        "updated_log_law_ustar": updated_ustar,
        "stale_fft_roughness_reproduced": confirmed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if confirmed else 1)


if __name__ == "__main__":
    main()
