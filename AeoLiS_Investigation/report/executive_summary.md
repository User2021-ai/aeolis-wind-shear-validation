# Executive summary

## Bottom line

AeoLiS is well suited as a fast aeolian sediment-transport framework, but the audited `3.1.0rc1` wind module is not a general solver of wind flow over dunes. Its optional `fft` pathway predicts surface-shear perturbations using linear low-hill theory on a rotated interpolation grid, with an empirical separation envelope. It should be expected to perform best for smooth, low, attached-flow terrain and to degrade for steep, separated, strongly three-dimensional, oblique, heterogeneous, or boundary-truncated cases.

The investigation found correctness blockers that should be fixed before drawing scientific conclusions from a CFD comparison:

1. spatially varying aerodynamic roughness crashes the 2-D FFT shear path;
2. grid spacings `ds` and `dn` are swapped for 2-D grids, affecting non-square cells;
3. the current test suite contains no wind/shear physics tests;
4. the regression suite is not failure-isolated and currently reports 4 failures;
5. a later repository branch reports that rotated-grid boundaries produce 19% shear error on a Boschplaat case, compared with 0.5% for a padded model-grid spectral method;
6. separation-bubble geometry is repository-reported to depend on cell size and cannot represent signed recirculation.

The local manufactured checks confirm correct flat-bed and simple ridge limits, vertical-datum invariance, strong sensitivity to the configured single length scale `L`, and the adaptive-roughness crash.

## Strongest scientific opportunity

The most defensible postdoctoral program is not “replace AeoLiS with ML.” It is:

1. verify and repair the deterministic shear implementation;
2. quantify its error regime with analytical cases, RANS/LES, and field data;
3. improve boundaries, per-wavelength response, and separation physics;
4. learn the remaining structured residual with a physics-aware, rotation-consistent, uncertainty-aware surrogate;
5. validate the hybrid first on surface shear and only then on sediment transport and morphology.

## Expected largest errors

- sharp crests and lee slopes with persistent separation;
- barchans, parabolic dunes, blowouts, and oblique winds with secondary flow;
- topography containing multiple important wavelengths when one `L` is used;
- sloping beaches and features near FFT boundaries;
- spatial roughness transitions and vegetation patches;
- non-square or under-resolved grids;
- non-neutral or highly unsteady atmospheric conditions.

## Recommended first three actions

1. Build a shear-specific test suite and fix the spatial-roughness and grid-metric defects.
2. Reproduce the repository-reported 19% vs 0.5% boundary result with archived inputs and metrics.
3. Run a canonical CFD matrix across steepness and yaw, measuring vector stress, phase, separation onset, and reattachment—not only wind speed or final morphology.

