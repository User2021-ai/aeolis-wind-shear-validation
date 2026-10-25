# CFD and field validation protocol

## 1. Validation philosophy

Use a hierarchy:

1. **Code verification** — is the mathematical algorithm implemented correctly?
2. **Solution verification** — are numerical errors from grid, domain, interpolation, and convergence controlled?
3. **Physics validation** — does the simplified model agree with CFD and field observations within a stated regime?
4. **Morphodynamic validation** — only after surface shear is credible, test transport and bed evolution.

Do not calibrate on the same cases used to claim validation. Do not use CFD as unquestioned truth: verify CFD mesh/domain/turbulence-model sensitivity and connect selected cases to field data.

## 2. Benchmark hierarchy

### Tier A — analytical and manufactured

- flat bed;
- single sinusoidal ridge aligned with wind;
- oblique sinusoidal mode;
- two superposed wavelengths;
- Gaussian low hill;
- constant vertical offset and translated feature;
- identical terrain rotated with wind/grid.

Purpose: signs, units, Fourier amplitude/phase, equivariance, boundaries, resolution.

### Tier B — canonical CFD

- smooth symmetric dune with `H/L` sweep;
- asymmetric dune with rounded crest;
- sharp-brink transverse dune;
- isolated barchan;
- parabolic dune;
- blowout/depression;
- two-dune interaction with spacing sweep;
- sloping beach plus dune;
- roughness step with and without topography.

### Tier C — measured topographies

- repeat lidar/photogrammetry DEMs at field sites;
- colocated wind profiles and surface-shear proxies;
- cases spanning attached, intermittent separation, and persistent separation.

## 3. Factorial case matrix

| Factor | Suggested levels |
|---|---|
| `H/L` | 0.01, 0.025, 0.05, 0.10, 0.20 |
| maximum lee slope | 5°, 10°, 15°, 20°, 25°, 30°, 35° |
| yaw angle | 0°, 15°, 30°, 45°, 60°, 75°, 90° |
| `z0/H` | at least 3 logarithmically spaced values |
| boundary-layer thickness `delta/H` | 2, 5, 10, 20 |
| turbulence intensity | low, field-median, high |
| topographic 3-D aspect ratio | ridge, weakly 3-D, strongly 3-D |
| dune spacing | isolated, 2H, 5H, 10H |
| AeoLiS grid cells per `L` | 10, 20, 40, 80 |

Use a space-filling subset for expensive LES, but retain structured sweeps for interpretable regime boundaries.

## 4. CFD setup

### RANS screening

- incompressible neutral atmospheric boundary layer;
- steady RANS, initially `k-omega SST`, with a documented rough-wall treatment;
- inlet velocity, turbulence, and roughness consistent with the same log law;
- upstream fetch sufficient for equilibrium profiles;
- top boundary outside the terrain-disturbed layer;
- outlet sufficiently downstream of reattachment;
- lateral periodic boundaries for infinite ridges, open/wide boundaries for 3-D dunes;
- second-order discretization and strict residual/integral convergence.

### LES/IDDES escalation

Use for selected separated cases where RANS model-form uncertainty is large. Run long enough for converged mean shear and separation statistics. Report sampling uncertainty.

### Mesh evidence

- at least three systematically refined meshes;
- wall-normal resolution consistent with the wall model (`y+` target reported);
- refinement near crest, brink, separation shear layer, and reattachment;
- grid-convergence index or equivalent uncertainty;
- domain-size sensitivity distinct from mesh sensitivity.

## 5. Mapping CFD to AeoLiS

1. Express coordinates and wind convention explicitly.
2. Extract wall shear vector `(tau_x, tau_y)` on the terrain.
3. Define the same flat-bed reference `tau0` from a companion CFD case.
4. Compare normalized perturbations, not only dimensional stress.
5. Conservatively remap CFD wall fields to the AeoLiS grid; repeat at native and remapped resolution.
6. Mask cells where terrain discretization is not comparable.
7. Separate attached and separated regions using CFD wall-shear sign/streamlines.

## 6. Field design

Recommended measurements:

- repeated high-resolution lidar or structure-from-motion DEM;
- upstream reference mast with multi-level sonic anemometers;
- crest, stoss, lee, and reattachment sonic arrays;
- near-surface Reynolds-stress estimates where feasible;
- surface-shear proxies such as calibrated drag plates, Irwin sensors, or profile-derived `u_*`;
- turbulence intensity, direction variability, temperature stratification, and roughness state;
- vegetation height/density and moisture to identify confounding periods;
- synchronized timestamps and common coordinates.

Field exclusion/stratification rules should be predeclared for precipitation, nonstationarity, strongly non-neutral stability, rapidly changing vegetation/roughness, and wind-direction sectors contaminated by instruments or distant obstacles.

## 7. Metrics

### Point/field magnitude

```math
NBIAS = \frac{\overline{\tau_A-\tau_R}}{\overline{\tau_R}}, \qquad
NRMSE = \frac{\sqrt{\overline{(\tau_A-\tau_R)^2}}}{\overline{\tau_R}}.
```

Also report median absolute error, 90th percentile error, correlation, and structural similarity.

### Vector direction

```math
\Delta\theta = \operatorname{atan2}(\tau_{A,x}\tau_{R,y}-\tau_{A,y}\tau_{R,x},
\tau_{A,x}\tau_{R,x}+\tau_{A,y}\tau_{R,y}).
```

Report circular mean bias and circular absolute error.

### Topographic-flow diagnostics

- peak speed-up `max(tau/tau0)`;
- location of peak relative to crest, normalized by `L`;
- complex Fourier transfer amplitude and phase;
- separation-onset location;
- reattachment length `x_r/H`;
- area fraction with reversed wall shear;
- wake-deficit recovery length;
- integrated stress over stoss/crest/lee zones.

### Uncertainty-aware score

Use combined observational, CFD, remapping, and numerical uncertainty. A discrepancy smaller than combined uncertainty is not evidence of model bias.

## 8. Error attribution experiments

Use nested comparisons:

1. Weng equation on an ideal periodic grid.
2. Current AeoLiS rotated-grid implementation.
3. Model-grid spectral implementation.
4. CFD attached-flow result.
5. CFD separated-flow result.
6. Field observation.

This separates transfer-function error from rotation/interpolation error, boundary error, separation closure error, CFD model error, and field representativeness error.

## 9. Predeclared regime map

Fit error as a function of dimensionless predictors, with interactions:

```math
E = f(H/L,\;slope,\;curvature,\;yaw,\;z_0/H,\;\delta/H,\;TI,\;stability,\;resolution).
```

Report contours defining, for example, `NRMSE < 10%`, `10–25%`, and `>25%`, plus separation-location tolerance. Thresholds should be agreed before looking at the full validation set.

