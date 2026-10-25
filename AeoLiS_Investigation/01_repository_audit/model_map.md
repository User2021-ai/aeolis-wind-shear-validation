# Repository and model map

## Audited baseline

- Repository: `https://github.com/openearth/aeolis-python`
- Branch: `main`
- Commit: `1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`
- Package version: `3.1.0rc1`
- Local clone: `source/aeolis-python`

The repository is a process-based aeolian sediment-transport model. Topographic wind feedback is optional: `process_shear` defaults to `False`, while `method_shear` defaults to `fft` if shear is enabled.

## Relevant execution path

| Stage | Main code | Function |
|---|---|---|
| Read/convert wind | `aeolis/wind.py` | `initialize`, `interpolate` |
| Compute roughness | `aeolis/wind.py` | `calculate_z0` |
| Flat-bed `u_*` and `tau` | `aeolis/wind.py` | `interpolate`, `velocity_stress` |
| Select shear method | `aeolis/wind.py` | `initialize`, `shear` |
| Rotated FFT grid | `aeolis/shear.py` | `WindShear.__call__`, `set_computational_grid` |
| Weng transfer | `aeolis/shear.py` | `compute_shear` |
| Separation envelope | `aeolis/shear.py` | `separation`, `separation_shear` |
| 1-D alternatives | `aeolis/wind.py` | `compute_shear1d`, `Kroy2002`, `compute_shear_perturbation_kroy1D` |
| Grid metrics | `aeolis/gridparams.py` | `initialize` |
| Time stepping | `aeolis/model.py` | `set_timestep`, `run` |

## Current wind/shear algorithm

1. Convert nautical/cartesian wind direction and decompose reference velocity into grid components.
2. Convert wind speed at measurement height `z` into flat-bed friction velocity using a log law.
3. Build a rectangular computational grid aligned with the wind.
4. Interpolate bed topography and reference stress to this grid.
5. Optionally build a cubic separation envelope over steep lee slopes.
6. Apply a 2-D FFT and the Weng et al. transfer function.
7. Add dimensionless stress perturbations to the reference stress.
8. Clip negative along-wind stress to zero.
9. Attenuate both stress components under the separation envelope.
10. Rotate/interpolate the result back to the model grid.

## What the model does not calculate

The current `fft` path does not solve:

- pressure, vertical velocity, turbulence kinetic energy, or Reynolds stresses;
- vertical profiles of the perturbed flow;
- atmospheric stability or a time-dependent boundary layer;
- explicit flow reversal inside a recirculation zone;
- wake interaction derived from Navier–Stokes dynamics.

Therefore, CFD comparison should focus first on wall shear stress and carefully derived near-bed diagnostics, not on treating AeoLiS as a full flow solver.

## Alternative implementations already visible in repository history

- `origin/OpenFoam_wind_shear` contains an experimental file-based route for importing OpenFOAM velocity and friction-velocity components. It is prototype-quality and is not integrated into `main`.
- `origin/aeolis-claude` contains a newer model-grid spectral method (`fft_grid`), separation on the model grid, multiple transfer functions, and extensive notes on known problems. It is explicitly described there as a review branch, not a merge-ready release.

These branches are valuable design evidence, but results from them should not be attributed to the audited `main` baseline.

