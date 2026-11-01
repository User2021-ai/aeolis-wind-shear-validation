# B01 — How surface roughness reaches the FFT shear calculation

AeoLiS uses aerodynamic roughness length, `z0`, to describe how the surface affects near-ground wind. On the audited AeoLiS 3.1.0rc1 revision (`1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`), two ways of describing the same surface produced different outcomes. Giving the FFT solver a single value of 0.001 m worked. Giving it a 64 × 64 grid with 0.001 m in every cell caused it to stop before it could return shear stress. [Reproducer](../07_reproducibility/scripts/b01_roughness_reproducer.py) · [Recorded results](../07_reproducibility/results/b01_roughness_results.json)

## Two failure modes

| Experiment on the audited source | Observation | Cause |
|---|---|---|
| Use a uniform or varying roughness grid on the same sinusoidal ridge | Both grids raise `ValueError` in `shear.py:607`. The scalar control returns finite shear. | The code divides a vector of 4,032 Fourier-mode values by a 64 × 64 array indexed by physical location. |
| Change scalar roughness from 0.001 m to 0.002 m between wind updates | The log-law friction velocity increases from 0.44515 to 0.48138 m/s. The FFT object still holds 0.001 m after the shear calculation. | The log law reads the current roughness. The FFT object retains the value supplied at initialization. |

A Fourier mode describes a terrain wavelength across the domain. A roughness cell describes one place on the ground. Flattening both arrays would make the arithmetic possible while assigning local roughness values to unrelated wavelengths. The controlled scalar experiment isolates a separate problem that can occur without an exception. [Wind-update trace](../07_reproducibility/results/b01_lifecycle_results.json)

## What the candidate patch does

In the patched checkout, the 2-D FFT solver accepts a positive finite scalar or a terrain-shaped field with exactly the same value in every cell. It converts the uniform field to its scalar equivalent and refreshes the value during wind updates. If even one cell differs, it raises an explanatory error. Predicting stress across real roughness transitions remains an open modelling question. [Patch](B01_full_model.patch)

## What we verified

The original failure reproducer and six tests of the standalone safeguard run in GitHub Actions. A separate local experiment exercised the patch through `AeoLiS.initialize()` and `AeoLiS.update()`. All ten focused checks passed. After three steps with active sediment transport, the patched scalar simulation matched the original arrays exactly. The equivalent uniform adaptive case matched within the stated tolerances. The varying-field case stopped before model time, sediment mass, or bed elevation changed. [Workflow](../../.github/workflows/reproducibility.yml) · [Full-model results](../07_reproducibility/results/b01_full_model.json)

The broader upstream suite returned 20 passes and the same four failing tests on the clean and development checkouts. The candidate is available in this research repository. Upstream review and physical validation against CFD or observations remain open.

## Reproduce the result

Start with the clean audited source and the project dependencies installed. Run `b01_roughness_reproducer.py --output b01-results.json` using the linked script. Its exit code is zero when the scalar control works and both grid inputs reproduce the known failure. To evaluate the correction, generate the scalar reference with the clean checkout, then run the integration harness against a separate patched checkout. The integration report gives the PowerShell commands, comparison tolerances, and individual outcomes. [Full-model integration report and reproduction instructions](B01_integration_plan.md)
