# Physics-aware machine-learning surrogate plan

## Recommended target

Learn a correction to the analytical baseline, not surface stress from scratch:

```math
\boldsymbol{\tau}_{hybrid}
= \boldsymbol{\tau}_{AeoLiS}
+ \Delta\boldsymbol{\tau}_{ML}.
```

For separated flow, add a classification/regression head for separation probability and signed wall-shear state. This retains the interpretable low-slope solution while allocating model capacity to systematic residuals.

## Inputs

Use dimensionless or normalized fields:

- terrain elevation relative to a local reference;
- wind-aligned slope and cross-slope;
- curvature and multi-scale terrain filters;
- distance to crest/brink and local relief at several radii;
- reference stress vector and yaw angle;
- `z0/H_local`, boundary-layer thickness, turbulence intensity, and stability;
- AeoLiS baseline `delta tau`, separation envelope, and confidence flags;
- grid spacing and distance to domain boundaries.

Avoid raw absolute elevation unless atmospheric density or other elevation physics is explicitly included.

## Outputs

- residual along-wind and cross-wind stress;
- probability of separation;
- probability/sign of reversed wall shear;
- optional reattachment distance or wake-deficit field;
- predictive uncertainty.

## Candidate architectures

1. **Residual U-Net** — strong local/multiscale baseline, straightforward.
2. **Fourier neural operator** — natural for field-to-field mapping, but boundaries need careful encoding.
3. **Graph neural operator** — useful for curvilinear/unstructured terrain.
4. **Patch model plus streamline recurrence** — attractive for wake memory along wind.

Benchmark them against simpler baselines: linear correction, Gaussian process on diagnostic features, and calibrated transfer coefficients. Complex ML is justified only if it improves site-held-out performance.

## Physical structure

Enforce or penalize:

- zero correction on a flat homogeneous bed;
- translation invariance in horizontal coordinates;
- invariance to vertical datum;
- rotation/reflection consistency of vector outputs;
- continuous behaviour as slope approaches zero;
- stress magnitude bounds based on training physics;
- correct units through nondimensionalization;
- smoothness at resolved scales without erasing separation fronts;
- consistency between predicted stress magnitude and `u_*`;
- uncertainty inflation outside the training domain.

Do not impose nonnegative along-wind stress if the target includes recirculation; that would encode the current limitation into the surrogate.

## Loss function

One possible composite loss is

```math
\mathcal L =
w_1\|\boldsymbol{\tau}-\boldsymbol{\tau}^{ref}\|_1
+w_2\|\nabla\boldsymbol{\tau}-\nabla\boldsymbol{\tau}^{ref}\|_1
+w_3\mathcal L_{angle}
+w_4\mathcal L_{sep}
+w_5\mathcal L_{spectral}
+w_6\mathcal L_{symmetry}
+w_7\mathcal L_{uncertainty}.
```

Use zone weights so large attached areas do not overwhelm the smaller but scientifically important crest, brink, and reattachment regions.

## Data splits

Never randomly split cells from the same CFD field across train and test. Use grouped splits:

- hold out entire geometries;
- hold out yaw sectors;
- hold out steepness ranges;
- hold out complete field sites;
- reserve a final blind benchmark untouched by architecture selection.

## Multi-fidelity strategy

- many inexpensive RANS cases for broad coverage;
- selected LES cases to correct RANS separation bias;
- field data for domain adaptation and final validation;
- fidelity indicator and uncertainty model;
- active learning selecting cases where ensemble disagreement is high and scientific coverage is sparse.

## Deployment safeguards

The surrogate should return both prediction and applicability diagnostics. Fall back to the analytical model or request CFD when inputs exceed training ranges in slope, yaw, roughness, stability, resolution, or terrain spectrum.

## Success criteria

- materially lower vector NRMSE than AeoLiS on site-held-out cases;
- improved peak location and reattachment length;
- no degradation in the low-slope analytical regime;
- calibrated uncertainty with high coverage of true error;
- stable coupled morphodynamics without artificial grid-scale growth;
- speed at least two orders of magnitude faster than the reference CFD workflow for operational domains.

