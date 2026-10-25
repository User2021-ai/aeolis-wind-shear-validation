# AeoLiS wind-flow and shear-stress investigation

This folder is a research workspace for evaluating AeoLiS against CFD and field observations. It is based on `openearth/aeolis-python` commit `1fcbe86d173f964e6ee231c0ee917ca3a6cd3f5e` (`main`, version `3.1.0rc1`, 17 April 2026).

## Start here

1. [Executive summary](report/executive_summary.md)
2. [Technical report](report/technical_report.md)
3. [Research questions and hypotheses](00_project_scope/research_questions.md)
4. [Prioritized bug and limitation register](03_bug_register/bug_register.md)
5. [CFD and field validation protocol](04_validation/cfd_field_validation_protocol.md)
6. [Physics-aware ML plan](05_ml_surrogate/physics_aware_ml_plan.md)
7. [Development roadmap](06_development_roadmap/roadmap.md)

## Folder map

```text
AeoLiS_Investigation/
├── 00_project_scope/       research framing, hypotheses, definitions
├── 01_repository_audit/    code map, branch evidence, test status
├── 02_physics_math/        equations, assumptions, dimensional analysis
├── 03_bug_register/        confirmed bugs, risks, hypotheses, priorities
├── 04_validation/          CFD/field experiment design and metrics
├── 05_ml_surrogate/        hybrid surrogate design and safeguards
├── 06_development_roadmap/ staged implementation and decision gates
├── 07_reproducibility/     executable checks and machine-readable results
├── 08_references/          provenance and literature-search plan
└── report/                 executive and technical reports
```

## Evidence labels

- **Confirmed**: directly reproduced or unambiguous from executable code.
- **Repository-reported**: stated in another repository branch or commit, but not independently recreated here.
- **Model limitation**: expected consequence of the chosen theory, not necessarily a programming error.
- **Hypothesis**: plausible issue requiring a targeted test or primary-literature check.

This distinction is important: disagreement with CFD is not automatically a software bug, and a code path that runs without crashing is not automatically physically valid.

## Reproduce the local shear checks

From the cloned `source/aeolis-python` directory, with AeoLiS and its dependencies installed:

```powershell
python ..\..\AeoLiS_Investigation\07_reproducibility\scripts\shear_sanity_checks.py `
  --output ..\..\AeoLiS_Investigation\07_reproducibility\results\shear_sanity_results.json
```

The current result is stored in [shear_sanity_results.json](07_reproducibility/results/shear_sanity_results.json).

