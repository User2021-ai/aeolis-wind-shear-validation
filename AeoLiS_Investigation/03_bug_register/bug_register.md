# Prioritized bug, risk, and limitation register

Priority combines scientific impact, likelihood, and how broadly the issue affects simulations. Line numbers refer to the audited commit and may move in later revisions.

## Priority 0 — must resolve before scientific validation

| ID | Type | Finding and evidence | Impact | Recommended action |
|---|---|---|---|---|
| [B01](B01_spatial_roughness_failure.md) | **Confirmed bug** | Spatially variable `z0` crashes FFT shear. `wind.calculate_z0` may return a 2-D array; `shear.compute_shear` indexes `z0new` with a Fourier mask but leaves `l` as a 2-D array. Reproduced as `ValueError: operands could not be broadcast together with shapes (4032,) (64,64)`. | Adaptive roughness cannot be combined reliably with 2-D FFT shear. | Define the intended physics first: local transfer approximation, effective scalar `z0`, or a nonstationary operator. Add scalar/field tests. |
| B02 | **Confirmed bug** | `aeolis/gridparams.py:203-204` assigns column spacing to `dn` and row spacing to `ds`. The repository's later branch also lists this as an open issue. | Non-square cells distort advection, CFL, gradients, areas, and shear-grid setup. | Correct names, add rectangular-grid manufactured tests, and quantify changes to existing cases. |
| B03 | **Repository-reported numerical defect** | Rotated FFT edges wrap around. A sloping beach can become a false cliff; interpolation also smooths/shifts stress. The later branch reports 19% shear error on Boschplaat versus 0.5% for a padded model-grid operator. | Large spatially coherent false erosion/deposition patterns near boundaries. | Reproduce the benchmark, document norm/region, then replace or deprecate the old rotated-grid method. |
| B04 | **Confirmed verification gap** | No unit tests target wind/shear equations, separation, rotation, adaptive roughness, or CFD/analytical benchmarks. | Regressions and scientifically wrong outputs can pass CI. | Build a shear-specific verification suite before refactoring. |

## Priority 1 — high scientific impact

| ID | Type | Finding and evidence | Impact | Recommended action |
|---|---|---|---|---|
| B05 | **Repository-reported bug** | Separation-bubble size depends on grid-cell size. The code also uses hard-coded offsets such as `i+5` and `i-3`. | Reattachment and sheltered area change under mesh refinement. | Reformulate all look distances and derivatives in physical coordinates; require grid convergence. |
| B06 | **Model limitation** | Separation attenuates stress but never produces signed reversed flow; `tau_x` is clipped at zero in `shear.py:237-238`. | Recirculation direction, wake transport, and reattachment physics cannot match CFD. | Treat separation and recirculation as separate targets; add signed wall-shear/wake correction or surrogate. |
| B07 | **Confirmed numerical issue** | `WindShear.maxDiff` adds `abs(i-j)` to a coordinate-intercept difference (`shear.py:664-665`). This mixes a dimensionless index with coordinate units and inflates computed grid width/length. | Direction-dependent computational-domain size and resolution cost; possible interpolation differences. | Replace with `max(arr)-min(arr)` and add exact geometry tests. |
| B08 | **Model-form sensitivity** | One configured `L` is used for every Fourier wavelength. In the local 16 m sinusoid check, changing `L` 25→400 m changed RMS perturbation by a factor 1.53. | Tuning `L` can compensate one terrain scale while biasing others. | Test per-mode Weng scales and Fourrière–Claudin–Andreotti transfer against CFD. |
| B09 | **Confirmed configuration hazard** | `method_roughness=constant` uses `k=z0`; `constant_nikuradse` uses `z0=k/30`. | Factor-30 interpretation difference changes baseline shear and all thresholds. | Rename parameters, validate ranges, warn on ambiguous legacy use, record effective `z0` in output. |
| B10 | **Repository-reported time-step bugs** | Later branch documents that the limiter ignores erosion, includes avalanching, can be overwritten, rebounds immediately, and drifts past output/stop time. Current code uses `np.max(dzb)` and `while t <= tstop`. | Morphodynamics and reported end states depend on step history; an extra step can alter output. | Backport with isolated tests for erosion/rise, output times, and exact `tstop`. |

## Priority 2 — investigate and bound

| ID | Type | Finding and evidence | Impact | Recommended action |
|---|---|---|---|---|
| B11 | **Confirmed bug** | `erosion.py:118` uses `np.max(twl-zToe, 0)` where elementwise lower bounding requires `np.maximum`. For a scalar below the toe, the negative value survives and is squared. | Nonzero collision-driven erosion can be computed when water level is below the toe. | Replace with `np.maximum`; add below/equal/above-toe tests. |
| B12 | **Hypothesis** | The transverse Weng expression lacks the `K0` denominator that appears in an abandoned fix. Repository history shows it was deliberately reverted without a derivation in code. | Potential magnitude/phase bias in cross-wind stress. | Compare line-by-line with Weng 1991 and independent implementations; do not patch from symmetry alone. |
| B13 | **Confirmed discontinuity** | Cardinal wind directions are perturbed (`0→0.01`, `270→270.01`, and exact grid angles by 0.1°) to avoid division by zero. | Tiny but systematic direction bias and discontinuity near cardinal directions. | Remove slope-based geometry singularities using vector/`atan2` formulations. |
| B14 | **Confirmed boundary risk** | Separation uses negative indexing near a brink (`i-3`) and ambiguous slices for reverse direction (`i+idir*5:`). | Boundary cells can sample the opposite edge or miss the downstream search. | Explicit boundary guards and translated-dune tests. |
| B15 | **Model limitation** | Pure crosswind modes (`kx=0`) are forced to zero. This is consistent with the implemented along-wind linear theory but not a general 3-D flow result. | Missed lateral pressure gradients and secondary flow. | Quantify error versus yaw, aspect ratio, and planform curvature. |
| B16 | **Model limitation** | Separation begins only when local lee slope exceeds default 30°. Real adverse-pressure-gradient separation can occur based on integrated geometry and boundary-layer state. | Missed separation on smoother or curved foredunes; abrupt onset at a threshold. | Learn/derive onset from CFD labels using slope, curvature, pressure gradient proxies, and boundary-layer state. |
| B17 | **Potential dimensional defect** | Stress reduction is `clip(1-10 hsep,0,1)` with `hsep` in metres; zero stress occurs at 0.1 m envelope height independent of dune scale. | Scale-dependent behaviour and poor transfer between laboratory and field dunes. | Recover derivation/units; nondimensionalize with local dune height or inner-layer scale. |
| B18 | **Test-infrastructure bug** | Regression tests change working directory and fail to restore it on assertion failure. | Test results depend on order and obscure root causes. | Use `monkeypatch.chdir` or `try/finally`; make every path fixture absolute. |

## Priority 3 — maintenance and interpretation

| ID | Type | Finding | Action |
|---|---|---|---|
| B19 | Interpretation risk | `process_shear=False` by default means no topographic wind feedback even though `method_shear=fft` is configured. | Emit a clear startup summary of active physics. |
| B20 | Numerical maintenance | Rotation uses `numpy.matrix`, producing thousands of warnings in tests. | Convert to `ndarray`/`@`; verify sign convention. |
| B21 | Documentation gap | Current docs describe the rotating grid but do not give the implemented transfer equations, units, validity domain, or benchmark accuracy. | Publish equations and validation envelope. |
| B22 | Prototype risk | OpenFOAM import branch reads fields with debug code and reverses a previously fixed directional initialization in its diff. | Treat as a prototype; design a clean coupling interface and tests instead of merging directly. |

## Fix order

1. B04 test harness and canonical manufactured surfaces.
2. B01 and B02 correctness blockers.
3. Reproduce B03 and establish boundary-reference benchmarks.
4. B05/B06/B14/B17 separation redesign.
5. B08/B12 transfer-function study.
6. B09/B13 configuration and geometry cleanup.
7. B10/B11 morphodynamic correctness.

