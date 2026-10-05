# Architecture Drift

- Status: BP-06 and BP-07.01/.02 closed/audited; BP-07.03/B2 proposal policy active.
- Last refreshed: `2026-10-05 00:23:06` (America/Chicago).
- Scope: unresolved v2 design/implementation alignment and scoped successor boundaries.
- Active focus: campaign context/proposal boundary; declaration publication prerequisite mismatch requires owner direction.
- Next gate: BP-07.03/B2.03c declaration publication compatibility decision; actual compiler-owner compatibility verified. Semantic and Runtime execution authority remain separate.

## Active Findings

| Finding | Owner / trigger | Disposition |
|---|---|---|
| Decision declaration v1 requires its own Artifact ID before Data allocates it | BP-07.03/B2.03c prerequisite | Blocking integration mismatch; [versioned correction proposed](../Build%20Plans/BP-07/BP-07.03%20Declaration%20publication%20decision.md), owner direction pending; existing synthetic and historical evidence preserved |
| Scientific and target-host claims exceed developer fixture proof | BP-07 model evaluation, BP-08 scientific search, BP-09 selected deployment; SQ-01 quality views | Named future gates; synthetic receipts/vectors and completed campaigns do not establish science; deployment/K3s remains proposed |
| Starlette/httpx test-client deprecation | Dev tooling, dependency maintenance | Nonblocking; test-client warning is not a production failure |
| Frozen baseline manifest reports added v1/LICENSE from99d219c while recorded content hashes match | Repository baseline metadata; explicit owner-authorized baseline maintenance | No v1 edits made; not an active implementation blocker |

[BP-06 parent audit](BP-06_Knowledge_Evidence_Closeout.md) reconciles six accepted children. Protocol fixtures, receipt/correction integration, independent reconstruction and scoped views are implemented; old partial notes remain in [drift history](Architecture%20Drift%20History.md). Live-model quality, scientific efficacy and deployed operations retain separate gates.

Use [Development Process](../Development_Process.md) and the [audit template](../Templates/Plan%20Audit%20Template.md). Each discrepancy names evidence, boundary, blocking classification, owner and disposition. Aligned records with no follow-up belong in history.
