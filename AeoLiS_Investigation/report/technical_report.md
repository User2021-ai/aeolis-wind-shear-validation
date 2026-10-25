# Technical assessment of AeoLiS wind flow and surface shear

## 1. Purpose

This assessment organizes a research program around the question: where does AeoLiS surface-shear prediction remain accurate, where does it fail, why does it fail, and which discrepancies should be addressed by corrected numerics, improved deterministic physics, or a learned surrogate?

## 2. Audited evidence

The source audit covers `main` commit `1fcbe86` (`3.1.0rc1`), repository history and remote branches present in the clone, the documentation and bibliography, a full local test run, and new deterministic shear sanity checks. No broad external literature search was performed in this pass; primary-literature details beyond repository metadata remain to be verified.

## 3. Principal finding: define the prediction target correctly

The current model takes a reference wind, obtains flat-bed friction velocity from a neutral log law, and computes surface-stress perturbations from bed Fourier modes. It does not compute a 3-D wind field. The empirical separation step constructs a surface above the lee slope and reduces stress below it; it does not solve a reversed recirculating flow.

Consequently, the primary comparison target should be the wall-shear vector and its spatial phase. Velocity profiles, turbulence, and wake structure belong to CFD/field diagnostics that explain error, not variables that AeoLiS directly predicts.

## 4. Verified and suspected defects

Two code defects directly block credible experiments: adaptive `z0` fails in the FFT operator, and 2-D grid-spacing labels are swapped. A third major issue is supported by repository benchmark notes: the rotated computational grid introduces smoothing/shift and a false periodic cliff at open boundaries. The current branch also lacks physics tests, and its separation code includes hard-coded cell offsets, boundary-sensitive indexing, and a dimensional ambiguity in stress reduction.

Not every discrepancy is a bug. Zero response to pure crosswind modes, use of one boundary-layer length scale, and the inability to resolve recirculation follow from the simplified formulation. These need a validity map or new closure, not merely code cleanup.

## 5. Numerical evidence from this audit

For a 64×64 synthetic grid:

- flat bed produced exactly zero perturbation;
- an along-wind 16 m sinusoidal ridge produced finite along-wind perturbation and zero transverse perturbation;
- adding 37 m to the elevation datum changed stress by only `1.18e-13` maximum;
- changing configured `L` from 25 to 400 m changed RMS along-wind perturbation from `1.026` to `1.568`, a ratio of `1.53` for the same bed wave;
- spatially varying `z0` produced a broadcasting `ValueError`.

These tests verify useful invariants but do not establish physical accuracy. The perturbations must next be checked against the analytical complex transfer and independent CFD.

## 6. Validation design

The validation hierarchy begins with manufactured Fourier surfaces, advances to RANS steepness/yaw sweeps, escalates selected separated cases to LES/IDDES, and ends with synchronized field topography and turbulence/shear observations. Comparisons should report vector NRMSE/bias, angular error, crest phase, separation onset, reattachment length, reversed-shear area, and uncertainty.

The critical methodological choice is nested comparison: equation-only reference, current rotated implementation, model-grid spectral implementation, CFD, and field. That decomposition prevents a boundary interpolation error from being misdiagnosed as a failure of Weng theory, or a CFD turbulence-model bias from being learned as truth.

## 7. Development strategy

First fix tests and correctness blockers. Then reproduce the boundary benchmark and build a regime map. Deterministic improvements should consider a model-grid operator, wavelength-dependent transfer, physically scaled separation, signed wake correction, roughness-transition physics, and optional stability effects.

Only after deterministic residuals are measured should ML be introduced. The recommended surrogate predicts a correction to AeoLiS stress, plus separation/reversal and uncertainty. Training/test splits must hold out whole geometries, yaw sectors, and sites. Flat-bed, datum, rotation, low-slope, and uncertainty constraints should be explicit.

## 8. Answer to the research question

The repository alone cannot yet provide a defensible quantitative accuracy claim against CFD and field data. It does provide strong evidence for the expected structure of error:

- smallest for smooth, low, attached, well-resolved terrain away from boundaries;
- increasing with separation, 3-D shape, oblique flow, scale mixture, roughness heterogeneity, and numerical boundary influence;
- potentially amplified into much larger sediment-flux errors near the transport threshold.

The proposed program converts that qualitative conclusion into a quantitative, reproducible regime map and a principled hybrid surrogate.

