# Test and reproducibility audit

## Executed test suite

Environment:

- Python 3.12.14
- AeoLiS installed editable from the audited checkout
- command: `python -m pytest -q`

Result:

```text
4 failed, 20 passed, 3169 warnings in 33.89 s
```

Failures observed:

1. The netCDF regression comparison expected `y=0` for a 1-D case but the generated file contained `y=0.5`.
2. A preceding regression test changes the process working directory and does not restore it after failure; later tests then resolve `aeolis/tests/aeolis.txt` relative to the wrong directory and fail.
3. The output-generation regression failure is entangled with that changed working directory.

Interpretation:

- The first mismatch may be an outdated reference file or an unintended coordinate change. It needs a release decision, not an automatic reference update.
- The later failures demonstrate test isolation problems rather than three independent model defects.
- The warnings are dominated by `numpy.matrix` use in rotation code, plus deprecations and two invalid escape sequences.

## Critical coverage gap

There are no dedicated unit tests for:

- `WindShear.compute_shear`;
- rotation and interpolation invariance;
- separation onset and reattachment;
- flat-bed zero perturbation;
- sinusoidal transfer amplitude and phase;
- wind-direction quadrants and exact cardinal directions;
- spatially variable aerodynamic roughness;
- rectangular grid cells;
- FFT edge/padding behaviour;
- comparison with an analytical, CFD, or field benchmark.

The regression suite largely checks that outputs remain the same. That protects historical behaviour, but it cannot establish that historical behaviour is physically correct.

## Locally added sanity checks

The reproducibility script confirms:

- flat bed gives zero perturbation;
- a ridge varying only along the wind produces zero transverse perturbation;
- adding a constant vertical datum changes the result only at round-off level;
- cross-wind-only topography produces zero perturbation under the implemented linear theory;
- an adaptive, spatially varying `z0` field raises a broadcasting `ValueError`;
- changing configured `L` from 25 to 400 m changes RMS perturbation for a fixed 16 m bed wave by a factor of 1.53.

See [the JSON result](../07_reproducibility/results/shear_sanity_results.json).

## Minimum new verification suite

1. Mathematical unit tests for each transfer-function term.
2. Manufactured sinusoidal surfaces with known complex amplitude/phase.
3. Rotation-equivariance tests at 0°, 15°, 30°, 45°, 60°, 75°, and 90°.
4. Boundary-placement tests for the same dune translated through the domain.
5. Grid-convergence tests in `dx`, `dy`, padding width, and domain size.
6. Separation tests with known brink and reattachment geometry.
7. Non-square-cell tests (`ds != dn`).
8. Scalar and spatial `z0` tests.
9. CFD reference snapshots with tolerances on magnitude, direction, phase, and reattachment.
10. Test-order randomization and automatic restoration of working directory.

