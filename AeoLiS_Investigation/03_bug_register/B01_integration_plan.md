# B01: roughness lifecycle and integration requirements

Audited source: AeoLiS commit `1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`.
Investigation date: 31 October 2026. Status: integrated and exercised in a separate local checkout of the audited revision. Upstream review remains pending.

## Integration experiment

The [candidate patch](B01_full_model.patch) changes `aeolis/shear.py` and `aeolis/wind.py`. The FFT constructor accepts a positive finite scalar or an exactly uniform field shaped like the terrain. The wind update passes the current validated roughness to both the log law and the FFT object. Direct shear calls recalculate roughness as well, which repeats a grain-size calculation in the normal adaptive update path. Runtime overhead on production grids remains unmeasured.

The [integration harness](../07_reproducibility/scripts/test_b01_full_model.py) creates a 12 by 8 synthetic dune grid and exercises `AeoLiS.initialize()` and `AeoLiS.update()`. Two equivalence cases advance through three 0.1 s steps. The original scalar run generated nonzero sediment flux and a maximum absolute bed change of approximately `9.49e-9 m`. This is a short regression fixture. Physical accuracy still requires independent reference data.

| Case | Observed result |
|---|---|
| Patched scalar versus original scalar | Final shear, friction velocity, flux components, concentration, mass and elevation arrays matched exactly. |
| Uniform adaptive versus original scalar | The same arrays agreed at relative tolerance `1e-12` and absolute tolerance `1e-14`. |
| Uniform two-fraction bed with a controlled change of surface grain composition | The next update refreshed FFT roughness and log-law friction velocity. |
| One cell changes composition | The FFT path raised a descriptive error before time, bed elevation or sediment mass changed. Wind input fields may already have been interpolated when the exception occurs. |
| Calm wind, disabled shear, and `duna2d` | The calm update refreshed roughness. Disabled shear and `duna2d` allowed a varying field. A calm-wind run emitted a divide warning in the model boundary-flux calculation. |

All ten focused checks passed, including direct-call cases. Both the original checkout and the patched checkout during development returned 20 passes and four failures in the upstream suite. The failing tests were the netCDF content check, output file generation, and two callback-path tests. The first content assertion compared the `y` coordinate in the `1D case1_small_waves` fixture. These failures remain open. [Saved focused results](../07_reproducibility/results/b01_full_model.json)

### Reproduce on a fresh checkout

From the research repository root, with its Python dependencies installed and `source/aeolis-python` at the audited commit, run the following in PowerShell. Use a fresh destination for the patched copy.

```powershell
$patch = (Resolve-Path AeoLiS_Investigation/03_bug_register/B01_full_model.patch).Path
$test = 'AeoLiS_Investigation/07_reproducibility/scripts/test_b01_full_model.py'
git clone --local source/aeolis-python source/aeolis-b01-review
git -C source/aeolis-b01-review apply --check $patch
git -C source/aeolis-b01-review apply $patch
New-Item -ItemType Directory -Force tmp | Out-Null
$env:PYTHONPATH = (Resolve-Path source/aeolis-python).Path
.venv/Scripts/python.exe $test --baseline tmp/b01-original.npz
$env:PYTHONPATH = (Resolve-Path source/aeolis-b01-review).Path
.venv/Scripts/python.exe $test --reference tmp/b01-original.npz --output tmp/b01-full-model.json
```

## Where roughness goes

| Stage | Audited source | Behavior |
|---|---|---|
| Model initialization | `model.py:254` | Calls `wind.initialize` |
| Wind initialization | `wind.py:71-79` | Computes roughness and constructs `WindShear` with it |
| FFT object initialization | `shear.py:142` | Stores roughness as `self.z0` |
| Each model update | `model.py:304` | Calls `wind.interpolate` |
| Log-law update | `wind.py:142-145` | Recomputes roughness and uses it in friction velocity |
| Nonzero-wind update | `model.py:309-310` | Calls `wind.shear` after rotating the grid |
| FFT branch | `wind.py:251-262` | Calls the existing shear object without passing new roughness |
| Spectral calculation | `shear.py:553` | Reads the stored `self.z0` |

There is no assignment refreshing the FFT object's `z0` in this update path. This matters for integration: validating roughness only when constructing the object cannot ensure that later roughness values reach the topographic transfer.

## Controlled lifecycle experiment

The [trace script](../07_reproducibility/scripts/b01_lifecycle_trace.py) calls the real `wind.initialize`, `wind.interpolate`, and `wind.shear` functions. It initializes a small sinusoidal terrain with scalar `z0 = 0.001 m`, changes the constant-roughness parameter to `0.002 m`, and exercises the next wind update and shear calculation.

This controlled parameter change isolates propagation of roughness. It is not a claim that a user normally changes `k` while a model runs, or an end-to-end adaptive-grain experiment. Adaptive roughness requires additional tests of changing bed composition.

Reproduction from the research repository root, using the project environment:

```powershell
$env:PYTHONPATH = (Resolve-Path 'source/aeolis-python').Path
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'aeolis-b01-mpl'
.venv/Scripts/python.exe AeoLiS_Investigation/07_reproducibility/scripts/b01_lifecycle_trace.py --output AeoLiS_Investigation/07_reproducibility/results/b01_lifecycle_results.json
```

The [result file](../07_reproducibility/results/b01_lifecycle_results.json) records initial and updated values. Exit zero means the stale-value behavior was reproduced, not that the issue was fixed.

Observed on the audited checkout: log-law roughness changed from `0.001 m` to `0.002 m`, and friction velocity changed from `0.44515 m/s` to `0.48138 m/s`. The FFT object still held `0.001 m` after `wind.shear` completed. This confirms the mismatch for the controlled update path.

## Proposed integration design

1. Validate and normalize roughness before constructing the FFT object. Preserve scalar values; collapse exactly uniform fields; reject varying fields explicitly.
2. During each wind update, compute the current roughness and apply the same validation before using it in the FFT branch. Share that calculated value where practical, avoiding duplicate adaptive calculations.
3. Refresh the FFT object's scalar `z0` with the validated current value before its next calculation. Keep local log-law roughness semantics explicit.
4. Restrict the safeguard to the two-dimensional FFT option. Other shear methods and runs with topographic shear disabled need their existing behavior preserved.
5. Add defensive validation for direct `WindShear` callers so bypassing the model configuration does not reintroduce B01.

Validation should happen before mutating the relevant wind state, so an unsupported update does not partly advance wind calculations. A later heterogeneous-roughness formulation needs a separate physical design; this safeguard must not silently average spatial variation.

## Acceptance tests before calling integration complete

- A scalar-roughness full run matches the original shear, transport, and bed evolution.
- An exactly uniform adaptive field matches the equivalent scalar run for several updates.
- A uniform roughness change updates both the log-law calculation and FFT object.
- A field that becomes spatially varying is rejected clearly before the unsupported shear calculation.
- Zero-wind steps, disabled shear, and non-FFT methods follow their intended paths.
- Existing upstream tests and representative examples pass, with any changed behavior explained.

The present lifecycle experiment covers real wind component calls, including rotated-grid shear, but does not call `model.update`, evolve sediment, or establish full-run equivalence. It supplies evidence needed to build those integration tests.
