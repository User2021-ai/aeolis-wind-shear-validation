# AeoLiS wind-shear validation study

This repository presents an independent, reproducible preliminary assessment of the wind-flow and surface-shear parameterizations in [AeoLiS](https://github.com/openearth/aeolis-python). It develops a research framework connecting analytical verification, high-resolution CFD, field measurements, and a physics-aware machine-learning surrogate.

> **Status:** preliminary research audit. This is not an official AeoLiS evaluation and is not affiliated with the AeoLiS development team. Findings are explicitly separated into reproduced defects, repository-reported issues, model-form limitations, and hypotheses requiring further validation.

## Scientific questions

1. How accurately does AeoLiS predict surface-shear magnitude, direction, spatial phase, and separation-induced reduction over coastal dune topography?
2. Under which combinations of steepness, three-dimensionality, wind obliquity, roughness, boundary-layer state, and numerical resolution are errors largest?
3. Can systematic CFD/field residuals support a rotation-consistent, uncertainty-aware surrogate without losing correct analytical limits?

## Current contributions

- source-level map of the AeoLiS wind/shear implementation;
- detailed equations and validity assumptions;
- evidence-graded bug and limitation register;
- deterministic FFT shear sanity checks;
- CFD and field-validation protocol;
- benchmark matrix and quantitative metrics;
- physics-aware residual-surrogate design;
- staged scientific development roadmap.

## Start here

- [Executive summary](AeoLiS_Investigation/report/executive_summary.md)
- [Technical report](AeoLiS_Investigation/report/technical_report.md)
- [Research questions and hypotheses](AeoLiS_Investigation/00_project_scope/research_questions.md)
- [Mathematical formulation](AeoLiS_Investigation/02_physics_math/wind_shear_equations.md)
- [Evidence-graded register](AeoLiS_Investigation/03_bug_register/bug_register.md)
- [CFD and field-validation protocol](AeoLiS_Investigation/04_validation/cfd_field_validation_protocol.md)
- [Physics-aware ML plan](AeoLiS_Investigation/05_ml_surrogate/physics_aware_ml_plan.md)
- [Development roadmap](AeoLiS_Investigation/06_development_roadmap/roadmap.md)

## Evidence policy

| Label | Meaning |
|---|---|
| Confirmed | Directly reproduced or unambiguous in executable code |
| Repository-reported | Described in upstream history but not independently recreated here |
| Model limitation | Expected consequence of the chosen simplified theory |
| Hypothesis | Requires a targeted experiment or primary-source check |

Disagreement with CFD is not automatically a software bug, and stable execution is not evidence of physical validity.

## Reproduce the sanity checks

```powershell
python -m pip install -r requirements.txt
python AeoLiS_Investigation/07_reproducibility/scripts/shear_sanity_checks.py `
  --output shear_sanity_results.json
```

The audited reference result is stored in [the results folder](AeoLiS_Investigation/07_reproducibility/results/shear_sanity_results.json).

## Audited upstream version

The initial assessment targets AeoLiS `3.1.0rc1`, commit `1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e`. See [UPSTREAM.md](UPSTREAM.md) for provenance and scope.

## Limitations

This stage does not claim completed CFD or field validation. Numerical findings are preliminary until reproduced independently and discussed with upstream maintainers. Primary-literature verification of the exact transverse transfer formulation remains part of the planned work.

## Intended use

This repository is a scientific research portfolio and an evolving validation workspace. It is intended to support constructive collaboration with the AeoLiS community.

## License

This repository is licensed under the [GNU General Public License v3.0](LICENSE). AeoLiS is a separate upstream project distributed under the same license; its copyright remains with the AeoLiS contributors. See [UPSTREAM.md](UPSTREAM.md) for version, attribution, and provenance details.

