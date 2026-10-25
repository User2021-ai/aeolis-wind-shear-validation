# Benchmark tracking matrix

| Case ID | Geometry | Flow regime | Purpose | Reference | Status |
|---|---|---|---|---|---|
| A00 | flat bed | attached | zero perturbation | analytical | local check passed |
| A01 | 1-D sinusoid | attached | amplitude/phase and transverse zero | analytical transfer | partial local check |
| A02 | oblique sinusoid | attached 3-D mode | vector transfer and rotation | analytical transfer | finite-output check only |
| A03 | two wavelengths | attached | single-`L` limitation | analytical/CFD | planned |
| A04 | translated Gaussian | attached | boundary/translation invariance | extended-domain spectral reference | planned |
| B01 | smooth symmetric dune | attached→separated | slope threshold | RANS sweep | planned |
| B02 | sharp-brink ridge | separated | recirculation and reattachment | RANS + LES subset | planned |
| B03 | barchan | 3-D separated | steering and horns | RANS/LES | planned |
| B04 | parabolic dune | 3-D separated | yaw and vegetation-ready geometry | RANS | planned |
| B05 | blowout | 3-D separated | depression/wake interaction | RANS/LES | planned |
| B06 | beach+dune ramp | mixed | FFT edge artefact | extended-domain spectral + RANS | repository evidence; reproduce |
| B07 | roughness step | attached internal layer | heterogeneous `z0` | RANS/field | blocked by B01 |
| C01 | instrumented foredune | field | end-to-end surface shear | field observations | site selection needed |
| C02 | Boschplaat DEM | field/remote sensing | reproduce reported 19%→0.5% result | branch benchmark/lidar | data workflow needed |

For every completed row, archive configuration, terrain, raw reference field, remapping script, metrics, plots, software revision, and uncertainty statement.

