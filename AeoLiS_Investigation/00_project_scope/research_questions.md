# Research framing

## Recommended primary question

**How accurately does AeoLiS 3.1.0rc1 predict the magnitude, direction, spatial phase, and separation-induced reduction of surface shear stress over coastal dune topography relative to terrain-following CFD and field observations, and how do errors vary with topographic steepness, three-dimensionality, wind obliquity, aerodynamic roughness, atmospheric boundary-layer state, and numerical resolution?**

This wording is more testable than asking whether AeoLiS represents the full wind flow. The current AeoLiS `fft` method does not solve a three-dimensional velocity or pressure field. It maps a reference wind and a bed elevation field to a surface-shear perturbation using linear theory, plus an empirical separation envelope.

## Postdoctoral extension

**Can the systematic residual between AeoLiS and validated CFD/field shear stress be learned by a physics-aware, rotation-consistent and uncertainty-aware surrogate that preserves the correct flat-bed and attached-flow limits while improving predictions of acceleration, steering, separation, and recirculation over complex dunes?**

## Testable hypotheses

| ID | Hypothesis | Primary observable | Falsification test |
|---|---|---|---|
| H1 | For low, smooth, attached-flow hills, AeoLiS predicts normalized shear magnitude and crestward phase with useful accuracy. | `tau/tau0`, phase of maximum `tau` | Canonical sinusoidal/Gaussian hills with small `H/L` and slope |
| H2 | Error grows nonlinearly once lee slope and adverse pressure gradient produce separation. | separation onset, reattachment `x_r/H`, lee-side `tau` | Steepness sweep across attached/separated regimes |
| H3 | Error grows with three-dimensionality and oblique incidence because rotation/interpolation and a single along-wind theory cannot reproduce secondary flow. | shear direction error and cross-wind component | Yaw sweep on barchan, parabolic dune, blowout |
| H4 | A single configured hill length `L` biases multi-scale terrain because all Fourier modes share the same boundary-layer scales. | spectral transfer amplitude and phase | Multi-frequency topographies and wavelength sweep |
| H5 | Boundary padding and periodic FFT assumptions create domain-edge artefacts on sloping beaches and truncated dunes. | edge-localized normalized error | Domain-length/padding/placement sweep |
| H6 | A hybrid residual surrogate generalizes better than a direct black-box predictor because the analytical baseline supplies the correct low-slope structure. | site-held-out error and physical constraint violations | Compare baseline, direct ML, and residual ML on identical splits |

## Causal chain under study

```text
reference wind + z0 + bed topography
                 ↓
log-law flat-bed friction velocity
                 ↓
FFT/Weng topographic shear perturbation
                 ↓
empirical separation envelope and stress reduction
                 ↓
surface shear velocity and direction
                 ↓
threshold, transport capacity, sediment flux
                 ↓
morphological change and feedback
```

The first validation stage should stop at surface shear. If wind errors and sediment-transport errors are calibrated together, compensating errors can make the final morphology look correct for the wrong reasons.

## Scope boundaries

Included:

- wind-to-surface-shear mapping;
- topographic acceleration and steering;
- separation-envelope and lee-side stress reduction;
- numerical rotation, interpolation, FFT boundaries, resolution, and roughness handling;
- CFD and field validation;
- a residual physics-aware surrogate.

Deferred until surface shear is credible:

- full recalibration of saltation/transport formulas;
- moisture, salt, groundwater, waves, and vegetation except where they alter aerodynamic roughness or shear partitioning;
- long-term morphodynamic skill scores.

## Required terminology

- `u_*`: friction or shear velocity, `sqrt(|tau|/rho_a)`.
- `tau0`: flat-bed reference surface shear stress vector.
- `delta tau`: dimensionless topographic perturbation added to `tau0`.
- acceleration: increase in along-wind surface stress over windward terrain.
- steering: change in surface-stress direction due to 3-D topography.
- separation: detachment of the mean near-surface flow from a steep lee slope.
- recirculation: reversed mean flow inside the separated region. The current AeoLiS method attenuates stress but does not resolve a signed recirculating velocity field.

