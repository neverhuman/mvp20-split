# Module and model status

Generated from `module-manifest.json`, `config/module-evidence-inventory.json`, and
each registered module's mission document. Regenerate with:

```bash
python3 scripts/generate-module-status.py --captured-at 2026-08-23
```

## Portfolio totals

| Statistic | Value |
|---|---:|
| Capture date | 2026-08-23 |
| Registered capability modules | 29 |
| `amphora-*` directories | 41 (15 workspace crates, 2 other code-bearing modules, 24 evidence/documentation trees) |
| Distinct declared adapter/model IDs | 15 |
| Ranking-eligible modules | 0 |
| Lanes | formulation=8, infrastructure=12, molecule=5, performance=4 |
| Operational readiness | AUDIT=2, BLOCKED=2, COMPLETE=12, GATED=3, OPEN=1, READY=2, ROADMAP=1, SHADOW=6 |
| Scientific readiness | UNVALIDATED=29 |
| Signed DSSE files | 568 |
| `CLAIM_REFUTED` mission verdicts | 58 |
| Retraction indexes | 22 |
| Supersession directories | 38 |
| Frozen campaign | 183 items (blocked=48, done=135) |

The adapter/model IDs below are declared runtime interfaces. They are not all separately
trained ML models: many are deterministic equations, policy gates, evidence validators, or
explicit unavailable-model sentinels. `Rank=no` is the important handoff fact: none currently
has authority to rank a real candidate.

## Per-module status

| Module | Lane | Implementation | Adapter/model ID | Model readiness | Ops | Science | Authority | Rank | Artifacts | Test pins | Refuted | Retraction | Benchmark |
|---|---|---|---|---|---|---|---|:---:|---:|---:|---:|:---:|---|
| amphora-barrier-corrosion-score | performance | amphora-barrier-corrosion-score/src/lib.rs | measured-eis-endpoints-v1 | MODEL_READINESS_ONLY | SHADOW | UNVALIDATED | MODELED_DIRECTIONAL | no | 5 | 1 | 4 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-candidate-contract | infrastructure | amphora-engine/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 10 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-cro-protocol-packager | infrastructure | amphora-assurance-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | CRO_GATED | no | 4 | 2 | 4 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-cure-potlife-gate | performance | amphora-cure-potlife-gate/src/lib.rs | cure-potlife-v1 | MODEL_READINESS_ONLY | BLOCKED | UNVALIDATED | CRO_GATED | no | 6 | 7 | 0 | yes | CHECKED_ARTIFACT_REPORTED_STATUS |
| amphora-design-rule-score | formulation | amphora-formulation-capabilities/src/lib.rs | directional-design-rule-v1 | MODEL_READINESS_ONLY | SHADOW | UNVALIDATED | RULE_CITED | no | 4 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-envelope-gates | formulation | amphora-formulation-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | REAL_ARITHMETIC | no | 3 | 2 | 3 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-evidence-intake-validator | infrastructure | amphora-assurance-capabilities/src/lib.rs | evidence-intake-authority-v1 | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 3 | 2 | 4 | yes | CHECKED_ARTIFACT_REPORTED_METRICS |
| amphora-formulation-arithmetic | formulation | amphora-formulation-capabilities/src/lib.rs | formula-arithmetic-envelope-v1 | R&D_RANKING_READY | COMPLETE | UNVALIDATED | REAL_ARITHMETIC | no | 3 | 2 | 4 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-formulation-universe | formulation | amphora-formulation-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | REAL_ARITHMETIC | no | 3 | 2 | 3 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-ingredient-library | formulation | amphora-formulation-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | GATED | UNVALIDATED | RULE_CITED | no | 3 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-ip-fto-guard | infrastructure | amphora-assurance-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | GATED | UNVALIDATED | EVIDENCE_ONLY | no | 1 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-known-answer-benchmarks | infrastructure | amphora-assurance-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | BLOCKED | UNVALIDATED | LIMITED_SANITY | no | 8 | 1 | 0 | yes | CHECKED_ARTIFACT_REPORTED_METRICS |
| amphora-model-card-authority | infrastructure | amphora-engine/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 1 | 1 | 4 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-molecule-generator | molecule | amphora-molecule-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | ROADMAP | UNVALIDATED | ROADMAP | no | 4 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-molecule-property | molecule | amphora-molecule-capabilities/src/lib.rs | molecule-reactive-function-v1 | MODEL_READINESS_ONLY | AUDIT | UNVALIDATED | REAL_ARITHMETIC | no | 6 | 1 | 5 | yes | CHECKED_ARTIFACT_REPORTED_METRICS |
| amphora-molecule-role-ranker | molecule | amphora-molecule-capabilities/src/lib.rs | molecule-role-fit-v1 | R&D_RANKING_READY | SHADOW | UNVALIDATED | LIMITED_SANITY | no | 6 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-molecule-novelty | molecule | amphora-molecule-capabilities/src/lib.rs | molecule-novelty-v1 | R&D_RANKING_READY | SHADOW | UNVALIDATED | LIMITED_SANITY | no | 0 | 1 | 0 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-molecule-design-gate | molecule | amphora-molecule-capabilities/src/lib.rs | molecule-design-gate-v1 | MODEL_READINESS_ONLY | READY | UNVALIDATED | REAL_ARITHMETIC | no | 0 | 1 | 3 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-optimizer-orchestrator | infrastructure | amphora-engine/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 0 | 3 | 0 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-process-qc-twin | performance | amphora-formulation-capabilities/src/lib.rs | process-qc-v1 | MODEL_READINESS_ONLY | OPEN | UNVALIDATED | EVIDENCE_ONLY | no | 2 | 1 | 6 | yes | CHECKED_ARTIFACT_REPORTED_METRICS |
| amphora-public-corrosion-benchmark | formulation | amphora-formulation-capabilities/src/lib.rs | corrosion-eis-v1 | MODEL_READINESS_ONLY | AUDIT | UNVALIDATED | EVIDENCE_ONLY | no | 38 | 1 | 0 | yes | CHECKED_ARTIFACT_REPORTED_STATUS |
| amphora-redteam-audit | infrastructure | amphora-assurance-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 2 | 2 | 0 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-report-packager | infrastructure | amphora-assurance-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 5 | 2 | 0 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-run-provenance | infrastructure | amphora-engine/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | EVIDENCE_ONLY | no | 1 | 1 | 5 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-solvency-score | formulation | amphora-solvency-score/src/lib.rs | carrier-solvency-tpd-v1 | MODEL_READINESS_ONLY | READY | UNVALIDATED | RULE_CITED | no | 4 | 1 | 5 | yes | CHECKED_ARTIFACT_REPORTED_METRICS |
| amphora-source-ledger | infrastructure | amphora-assurance-capabilities/src/lib.rs | — | MODEL_READINESS_ONLY | COMPLETE | UNVALIDATED | RULE_CITED | no | 4 | 2 | 3 | no | NO_CHECKED_BENCHMARK_RESULT |
| amphora-sourceability-ehs | infrastructure | amphora-assurance-capabilities/src/lib.rs | sourceability-evidence-v1 | MODEL_READINESS_ONLY | GATED | UNVALIDATED | EVIDENCE_ONLY | no | 25 | 1 | 3 | yes | NO_CHECKED_BENCHMARK_RESULT |
| amphora-tolerance-robustness | formulation | amphora-formulation-capabilities/src/lib.rs | formulation-robustness-v1 | MODEL_READINESS_ONLY | SHADOW | UNVALIDATED | LIMITED_SANITY | no | 5 | 1 | 0 | yes | CHECKED_ARTIFACT_REPORTED_STATUS |
| amphora-viscosity-score | performance | amphora-viscosity-score/src/lib.rs | viscosity-rheology-v1 | MODEL_READINESS_ONLY | SHADOW | UNVALIDATED | LIMITED_SANITY | no | 3 | 1 | 2 | yes | NO_CHECKED_BENCHMARK_RESULT |

`Artifacts` and `Test pins` are counts from the global evidence inventory, not payload row
counts. Read a module's `docs/mission.md` and retraction index before relying on a result.
The known stale source-lock exception remains documented in `BUILD.md`; this table does not
promote or reinterpret it.
