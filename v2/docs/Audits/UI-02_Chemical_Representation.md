# UI-02 chemical representation boundary audit

- Status: blocked on Registry policy; component gates verified.
- Reviewed: 2026-10-13 11:47:53 America/Chicago; baseline88bb5cb9.
- Owner: UI-02/P1. Overall18.75%, P1=75%, P2/P3/P4=0%.
- Next gate: actual Registry registration/activation, Runtime execution/retention,
  Data byte attribution, Research registration/replay/denial and mismatch rejection.
- Blocker: actual Registry activation_profile_denied; UI-02.02 owner decision required.

| Boundary | Evidence | Disposition |
|---|---|---|
| Additive public contracts |12 wire/publication checks;668 predecessor pins unchanged | aligned |
| Independent chemical tool |32 copied tests, schema bytes/fresh-process determinism, PNG inspected | aligned; actual handoff pending |
| Research opt-in identity |75 PostgreSQL/registration/identity tests,2 compatibility checks and dependency guard | aligned; actual Research handoff blocked upstream at Registry |
| UI formula/recommendation | Not implemented | P2-P4; do not imply viewer availability |
| Scientific claims | Supplied finite oligomer/structure only | No property, synthesis, clinical or ranking authority |

RDKit dependency is isolated to the tool. DTOs only validate transport; parsed
molecule/profile/display objects own behavior. No private peer imports or tables,
new Research migration or existing schema/receipt rewrite. PNG is inert, bounded,
source-bound and contains no metadata; Research validates header/hash/dimensions,
while full consumer decoding/attribution remains UI acceptance work.

Standalone isolated output: .test-results/ui02-chemical-independent-20261013a.
Six independent installations completed in .test-results/ui02-chemical-handoff-20261013a.
Original probe failed after rejected activation because the harness dereferenced a
missing accepted release. Corrected rerun b retains actual registered/rejected
receipts in [Registry evidence](Evidence/UI-02-Chemical/Registry_Activation.json).
Actual graph/tool/Data/Research portion did not run; no P1.4 credit.
The earlier activation inventory missed Registry's synthetic-only restriction.
[UI-02.02](../Build%20Plans/UI-02.02%20Structural%20tool%20registry%20profile%20decision.md)
specifies activation plus selection correction; no bypass or descriptor relabelling.
Declared fixture image pins must never be described as built Linux images or a
container deployment. Product hosting/containerization remains deferred per owner.
