# Development roadmap

## Phase 0 — freeze the evidence baseline (1–2 weeks)

Deliverables:

- pin commit, dependencies, and benchmark inputs;
- separate current `main` from experimental branches;
- establish shear-specific CI;
- reproduce current FFT fields for canonical cases;
- agree on variables, sign conventions, and error metrics.

Gate: every result is reproducible from a clean environment and tagged with code/data revisions.

## Phase 1 — repair correctness blockers (2–6 weeks)

Order:

1. fix test isolation;
2. add flat/sinusoid/rotation/boundary tests;
3. resolve `ds`/`dn` swap for rectangular cells;
4. decide and implement spatial `z0` behaviour;
5. fix computational-grid geometry (`maxDiff`) and cardinal angles;
6. fix dune-erosion `np.max` issue;
7. backport time-step corrections with tests.

Gate: no known Priority-0 defect; convergence tests pass; changes documented as result-changing or result-preserving.

## Phase 2 — establish the wind/shear benchmark (1–4 months)

- reproduce the reported old-grid vs model-grid boundary comparison;
- implement common analysis scripts for AeoLiS, RANS, LES, and field data;
- complete Tier A analytical cases;
- run Tier B RANS matrix;
- select LES escalation cases;
- publish an initial error-regime map.

Gate: errors can be attributed to transfer theory, numerics, or separation closure rather than reported as one aggregate discrepancy.

## Phase 3 — improve deterministic physics (3–8 months)

Candidate improvements, evaluated one at a time:

- model-grid spectral operator with explicit open/periodic boundaries;
- wavelength-dependent transfer functions;
- dimensionally consistent separation envelope;
- signed lee-side wall-shear/wake parameterization;
- internal-boundary-layer treatment for roughness changes;
- optional stability correction;
- uncertainty/applicability flags in output.

Gate: each added mechanism improves blind cases without degrading the low-slope analytical regime.

## Phase 4 — field campaign and calibration (overlapping, 4–12 months)

- select 1–2 instrumented sites with repeated DEMs;
- pre-register filtering and uncertainty rules;
- collect multiple wind sectors and stability classes;
- calibrate only on designated events;
- validate on withheld events/sites.

Gate: field skill is consistent with CFD-derived regime boundaries within combined uncertainty.

## Phase 5 — physics-aware surrogate (6–15 months)

- create versioned multi-fidelity dataset;
- train simple residual baselines first;
- add rotation-consistent field model;
- add separation/reversal and uncertainty heads;
- run geometry/yaw/site-held-out tests;
- integrate behind a feature flag.

Gate: the surrogate beats deterministic AeoLiS and simple calibration on blind cases, is stable in coupled runs, and detects out-of-domain inputs.

## Phase 6 — morphodynamic validation (12–24 months)

- propagate shear uncertainty through transport threshold/capacity;
- compare event-scale flux and bed change;
- test whether improved shear reduces transport-parameter compensation;
- run long-term stability and conservation checks.

Gate: improvements persist at morphology level without retuning unrelated transport parameters for every site.

## Immediate backlog

| Rank | Task | Effort | Output |
|---:|---|---:|---|
| 1 | Add `tests/test_shear.py` manufactured cases | 2–4 days | CI safety net |
| 2 | Reproduce adaptive `z0` crash and choose intended formulation | 2–5 days | design note + fix |
| 3 | Fix/test `ds`/`dn` on rectangular grid | 2–4 days | correctness patch |
| 4 | Reproduce Boschplaat 19%/0.5% comparison | 1–2 weeks | trusted boundary benchmark |
| 5 | Derive/verify transverse Weng equation from primary source | 2–5 days | equation audit |
| 6 | Grid convergence of separation envelope | 1 week | quantified B05 |
| 7 | Canonical RANS smooth/steep dune sweep | 3–6 weeks | first regime map |
| 8 | Design clean CFD field-input interface | 1 week | schema and adapter |
| 9 | Select field site and sensor layout | 2–4 weeks | campaign plan |
| 10 | Residual-ML baseline on canonical CFD | after data | go/no-go evidence |

## Governance recommendations

- Tag changes that alter physics separately from refactors/performance changes.
- Require an equation/reference note for every physics-changing pull request.
- Store reference outputs with provenance and uncertainty, not just arrays.
- Never update regression references until the physical reason for the change is reviewed.
- Maintain a model-validity statement alongside release notes.

