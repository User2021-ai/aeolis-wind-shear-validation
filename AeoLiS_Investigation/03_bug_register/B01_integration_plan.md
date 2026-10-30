# B01: roughness lifecycle and integration requirements

Audited source: AeoLiS commit `1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`.
Investigation date: 31 October 2026. Status: lifecycle investigation; full-model integration pending.

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
