# B01: spatially variable roughness crashes the FFT shear operator

## Classification

- Status: **confirmed and reproducible**
- Severity: Priority 0 for heterogeneous-roughness simulations
- Audited version: AeoLiS `3.1.0rc1`
- Audited commit: `1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`
- Reproducer: `../07_reproducibility/scripts/shear_sanity_checks.py`

## Plain-language summary

AeoLiS can calculate a different aerodynamic roughness length for every grid cell when adaptive grain-size roughness is enabled. The wind-shear component appears to accept that two-dimensional field, but its FFT calculation assumes that the transfer parameters are spatially uniform. During the calculation, a vector of Fourier modes is combined with a two-dimensional physical-space array, so Python stops with an incompatible-shape error.

This means the audited configuration does not merely produce an uncertain answer: it cannot complete the topographic shear calculation. It also means that removing the exception by forcing the arrays to have matching shapes would not, by itself, provide a physically correct solution.

### What is established

- The exception is deterministic and locally reproducible.
- The shape mismatch and its code path are identified.
- Scalar roughness continues to work in the same test harness.
- Adaptive roughness methods can supply the array shape that triggers the failure.

### What is not yet established

- How frequently real AeoLiS projects combine adaptive roughness with the FFT shear option.
- Whether maintainers intended a scalar effective roughness that is not currently enforced.
- Which heterogeneous-roughness formulation best matches CFD or field observations.
- Whether an equivalent issue has already been discussed outside the audited revision.

## Reproduce the finding

From the root of this research repository, install the pinned dependencies and run:

```powershell
python -m pip install -r requirements.txt
python AeoLiS_Investigation/07_reproducibility/scripts/shear_sanity_checks.py `
  --output shear_sanity_results.json
```

Inspect `spatially_variable_roughness` in the generated JSON. A scalar-roughness baseline should pass, while the spatial-field case records the exception shown below. The script captures the expected exception so that the overall command can finish and preserve the evidence.

## Minimal input

The reproducer constructs a `64 x 64` periodic sinusoidal ridge and supplies a spatial roughness field:

```python
import numpy as np
from aeolis.shear import WindShear

x, y = np.meshgrid(np.arange(64, dtype=float), np.arange(64, dtype=float))
wavelength = 16.0
ridge = 0.5 * np.cos(2.0 * np.pi * x / wavelength)
z0_field = 1.0e-3 * (
    1.0 + 0.25 * np.cos(2.0 * np.pi * x / wavelength)
)

model = WindShear(
    x, y, ridge,
    dx=1.0,
    dy=1.0,
    L=100.0,
    l=10.0,
    z0=z0_field,
    buffer_width=10.0,
)
model.igrid = {"x": x, "y": y, "z": ridge}
model.cgrid.update({"x": x, "y": y, "z": ridge.copy()})
model.x0, model.y0 = float(x.mean()), float(y.mean())
model.compute_shear(u0=10.0, nfilter=None)
```

This input shape is relevant to normal model use: `wind.calculate_z0` documents and returns two-dimensional roughness for adaptive grain-size methods such as `mean_grainsize_adaptive` and `median_grainsize_adaptive`.

## Expected behavior

One of the following contracts should be explicit and tested:

1. spatially variable `z0` is supported and produces a finite shear field using a physically defined heterogeneous-roughness formulation; or
2. the FFT operator rejects a roughness field immediately with a clear, actionable `NotImplementedError` or validation message explaining the supported scalar contract.

A low-level array-broadcasting exception is not an acceptable user-facing outcome.

## Actual behavior

The call fails with:

```text
ValueError: operands could not be broadcast together with shapes (4032,) (64,64)
```

The machine-readable reproduction is stored in `../07_reproducibility/results/shear_sanity_results.json`.

## Relevant code path

1. `aeolis/wind.py:195-199` returns a two-dimensional `z0` for adaptive roughness methods.
2. `aeolis/shear.py:561-564` accepts and interpolates a roughness array onto the computational grid.
3. `aeolis/shear.py:566-575` consequently calculates two-dimensional `l`, `hm`, and `ul` arrays.
4. `aeolis/shear.py:587` creates a two-dimensional Fourier-mode mask.
5. `aeolis/shear.py:595-604` flattens masked `k`, `kx`, `ky`, `hs`, and `z0` to vectors.
6. `aeolis/shear.py:607` combines the masked vector quantities with the unmasked two-dimensional `l`, producing the broadcasting failure. The same incompatibility would recur for `ul` at line 615.

## Why a simple indexing patch is insufficient

Changing `l` to `l[valid]` and `ul` to `ul[valid]` may remove the exception, but it would pair values defined at spatial grid cells with unrelated Fourier modes. Multiplication in physical space becomes convolution in Fourier space. Therefore, a pointwise spatial roughness field cannot be inserted into the stationary spectral transfer function merely by matching array shapes.

Such a patch could run without crashing while remaining physically and mathematically wrong.

## Scientific consequence

- Adaptive roughness cannot currently be combined reliably with the two-dimensional FFT shear method.
- Simulations involving sorting, armouring, vegetation proxies, or spatial roughness transitions may stop or be forced to use an undocumented scalar approximation.
- Roughness affects both the baseline logarithmic profile and the topographic transfer. Silently averaging it could bias stress amplification, phase, and threshold-crossing locations.
- Because sediment transport is strongly nonlinear near threshold, a local roughness/shear error can switch transport on or off and alter predicted erosion patterns.

## Proposed resolution

The recommended sequence is: implement the immediate safety correction first, agree with maintainers on the intended roughness contract second, and only then implement an approximation or new physical formulation. This avoids converting a visible crash into a silent scientific error.

### Immediate safety correction

- Validate `z0` at the FFT interface.
- If it is non-scalar, raise a clear error describing the incompatibility and supported alternatives.
- Add a configuration-level check so the model fails before time integration begins.

### Defined approximation, if scientifically justified

- Keep the local `z0(x,y)` for the flat-bed logarithmic stress calculation.
- Provide a separately named scalar effective roughness for the stationary topographic FFT transfer.
- Document how that scalar is calculated, its validity range, and its consequences near roughness transitions.
- Do not silently calculate it inside the operator.

### Full physical development

Represent heterogeneous roughness through an internal-boundary-layer or other nonstationary flow formulation, then validate it against CFD and field measurements. A spatially varying transfer operator will generally require more than a pointwise modification of Fourier coefficients.

## Proposed tests

1. Scalar `z0` regression: existing constant-roughness result remains unchanged.
2. Uniform array contract: either matches the equivalent scalar result or is rejected clearly, according to the chosen API.
3. Variable array contract: returns finite, validated results or raises the documented high-level exception.
4. Shape validation: incorrect roughness-grid shapes fail before interpolation.
5. End-to-end adaptive method: run at least one multi-fraction case with `process_shear=True`.
6. Physics benchmark: compare a roughness step and smooth roughness transition against CFD or field data, measuring stress magnitude, adjustment length, and phase.

## Suggested upstream communication

Open a focused issue before proposing a numerical implementation. Ask maintainers which behavior was intended for adaptive roughness with the FFT method and whether an effective scalar approximation exists in prior AeoLiS studies. Link the minimal reproducer and avoid presenting shape-only indexing as a valid fix.

## Focused B01 experiment (28 October 2026)

The [dedicated reproducer](../07_reproducibility/scripts/b01_roughness_reproducer.py) compares three representations on the same terrain: scalar roughness, a uniform array containing that same value, and a spatially varying array. It records the exception location, Python/NumPy/SciPy versions, and a SHA-256 fingerprint of the actual shear source file.

To reproduce against the local audited checkout from the research repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path 'source/aeolis-python').Path
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'aeolis-b01-mpl'
.venv/Scripts/python.exe AeoLiS_Investigation/07_reproducibility/scripts/b01_roughness_reproducer.py --output AeoLiS_Investigation/07_reproducibility/results/b01_roughness_results.json
```

This assumes the project dependencies have been installed in `.venv`. The local checkout is excluded from Git; other researchers can clone the upstream repository there and check out the audited commit listed above. Alternatively, omit `PYTHONPATH` to test their installed package, whose source fingerprint may differ.

The script exits successfully only if the scalar control is finite and both array cases reproduce the specific broadcasting error inside `compute_shear`. A successful run therefore confirms the known defect. It does not certify that the software is fixed. An unexpected outcome causes a nonzero exit and should be investigated.

Observed results against the clean audited checkout:

| Roughness input | Result |
|---|---|
| Scalar `0.001 m` | Finite shear output |
| Uniform `64 x 64` array, every value `0.001 m` | Broadcasting exception at `shear.py:607` |
| Varying `64 x 64` array, range `0.00075–0.00125 m` | Same exception at `shear.py:607` |

The [saved evidence](../07_reproducibility/results/b01_roughness_results.json) confirms that array representation alone is sufficient to trigger B01. Even a physically homogeneous roughness field fails when represented as a two-dimensional array. These are direct operator tests; full adaptive model runs remain a separate integration test.

For a future correction, a uniform field can be reduced to its identical scalar value without losing spatial information. A varying field requires an explicit modelling decision. This distinction should guide the eventual interface design; the present experiment does not modify the upstream solver.

## Proposed safeguard prototype (28 October 2026)

The local [roughness guard](../07_reproducibility/scripts/b01_roughness_guard.py) implements that input contract. It is an opt-in research helper, not an upstream AeoLiS fix. Callers pass its result as `z0` when constructing `WindShear`:

```python
z0_for_fft = scalar_fft_roughness(z0, ridge.shape)
```

| Input | Prototype behavior |
|---|---|
| Positive finite scalar | Preserve its value |
| Exactly uniform array matching the terrain | Convert to the identical scalar |
| Varying array | Raise a descriptive `NotImplementedError` |
| Wrong shape, nonpositive, nonfinite or non-real input | Raise `ValueError` |

Exact equality is deliberate: even a small variation is rejected rather than silently averaged. For a uniform field, conversion preserves all roughness information and uses the original scalar solver. Varying roughness remains unsupported; the prototype supplies no predictions for it. Positive roughness alone also does not guarantee validity of all logarithms or physical assumptions in the transfer formula.

Run the [six tests](../07_reproducibility/scripts/test_b01_roughness_guard.py) from the repository root after setting `PYTHONPATH` and `MPLCONFIGDIR` as above:

```powershell
.venv/Scripts/python.exe -m unittest discover -s AeoLiS_Investigation/07_reproducibility/scripts -p test_b01_roughness_guard.py -v
```

The tests compare the guarded uniform-grid result with the original scalar FFT result for both stress components, and cover varying grids, very small variations, wrong shapes and invalid values. Passing these checks establishes the prototype's input behavior and scalar equivalence. Integration into the full model and validation of heterogeneous roughness remain future work.

## Automated verification (30 October 2026)

The `b01-roughness` job in [the reproducibility workflow](../../.github/workflows/reproducibility.yml) checks out the exact audited AeoLiS commit and verifies that Python imports that checkout. On pushes and pull requests it then runs the three-case failure reproducer and the six safeguard tests. The safeguard tests still run if failure reproduction changes, provided the source verification succeeded.

The job saves the reproduction JSON and installed dependency versions as a `b01-evidence` artifact for 30 days. Dependencies other than AeoLiS are not fully locked; the environment record helps diagnose changes between runs. The committed local JSON remains a separate dated record.

A green B01 job means the known upstream failure was reproduced and the opt-in safeguard passed its tests. It does not mean heterogeneous roughness is physically validated or the safeguard is integrated into the upstream model. The older `shear-sanity` job only runs the diagnostic script and does not assert every reported result; its success alone must not be interpreted as proof that all checks passed.
