# Amphora MVP20 mission program

Amphora MVP20 contains 29 registered modules plus the root engine. The [module manifest](module-manifest.json) is the runtime policy registry; each canonical mission and machine-readable capability profile is bound from it.

Current runtime chemistry support is JSON plus molecule SMILES. The broader chemistry adapters in the profiles are targets and fail closed today. No module is promoted to Phase 1 or Phase 2 by documentation or unit tests.

See the [readiness crosswalk](docs/readiness-crosswalk.md) and [dependency-aware roadmap](docs/roadmap.md).

## Canonical missions

- [amphora-barrier-corrosion-score](amphora-barrier-corrosion-score/docs/mission.md)
- [amphora-candidate-contract](amphora-candidate-contract/docs/mission.md)
- [amphora-cro-protocol-packager](amphora-cro-protocol-packager/docs/mission.md)
- [amphora-cure-potlife-gate](amphora-cure-potlife-gate/docs/mission.md)
- [amphora-design-rule-score](amphora-design-rule-score/docs/mission.md)
- [amphora-envelope-gates](amphora-envelope-gates/docs/mission.md)
- [amphora-evidence-intake-validator](amphora-evidence-intake-validator/docs/mission.md)
- [amphora-formulation-arithmetic](amphora-formulation-arithmetic/docs/mission.md)
- [amphora-formulation-universe](amphora-formulation-universe/docs/mission.md)
- [amphora-ingredient-library](amphora-ingredient-library/docs/mission.md)
- [amphora-ip-fto-guard](amphora-ip-fto-guard/docs/mission.md)
- [amphora-known-answer-benchmarks](amphora-known-answer-benchmarks/docs/mission.md)
- [amphora-model-card-authority](amphora-model-card-authority/docs/mission.md)
- [amphora-molecule-design-gate](amphora-molecule-design-gate/docs/mission.md)
- [amphora-molecule-generator](amphora-molecule-generator/docs/mission.md)
- [amphora-molecule-novelty](amphora-molecule-novelty/docs/mission.md)
- [amphora-molecule-property](amphora-molecule-property/docs/mission.md)
- [amphora-molecule-role-ranker](amphora-molecule-role-ranker/docs/mission.md)
- [amphora-optimizer-orchestrator](amphora-optimizer-orchestrator/docs/mission.md)
- [amphora-process-qc-twin](amphora-process-qc-twin/docs/mission.md)
- [amphora-public-corrosion-benchmark](amphora-public-corrosion-benchmark/docs/mission.md)
- [amphora-redteam-audit](amphora-redteam-audit/docs/mission.md)
- [amphora-report-packager](amphora-report-packager/docs/mission.md)
- [amphora-run-provenance](amphora-run-provenance/docs/mission.md)
- [amphora-solvency-score](amphora-solvency-score/docs/mission.md)
- [amphora-source-ledger](amphora-source-ledger/docs/mission.md)
- [amphora-sourceability-ehs](amphora-sourceability-ehs/docs/mission.md)
- [amphora-tolerance-robustness](amphora-tolerance-robustness/docs/mission.md)
- [amphora-viscosity-score](amphora-viscosity-score/docs/mission.md)
