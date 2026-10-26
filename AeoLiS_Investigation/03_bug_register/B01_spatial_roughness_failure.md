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
