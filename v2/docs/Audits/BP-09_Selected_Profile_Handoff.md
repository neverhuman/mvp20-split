# BP-09 selected profile and evidence freeze

Design status: frozen bounded profile; final smoke/independent acceptance passed. Baseline `e40a8e4a`. Last reviewed `2026-10-07 10:52:01` (America/Chicago).

The [acceptance ledger](Evidence/BP-09-Deployment/Acceptance_Ledger.json) pins twelve
reviewed evidence files by SHA256 and rejects omitted/changed/failed gates. Frozen
evidence is historical: its exact release, scope, campaign and timing remain
authoritative. New evidence requires explicit review, not automatic hash refresh.
The checker does not claim to authenticate evidence or recursively validate every
raw artifact; original owner qualifications retain that responsibility.

| Criterion | Observed evidence | Claim boundary |
|---|---|---|
| Selected host/access | Workshop, Windows x86_64, loopback, one user/campaign | No remote DGX/Threadripper/cluster qualification |
| Independent owners | Six SQL owners plus gateway, separate packages/roles | Deployment never queries private peer tables |
| Context/model integration | Original `fc257cf8882147cb8cca56c778837e60`,15 invocations/6 evaluations/3 checkpoints | Synthetic numerical workflow; model abstention accepted, not arbitrary topology generation |
| Corrected information | Successor `6c124e88efec483ab6704ee096d6eb0c` | Future-campaign-only change; original immutable |
| Local capacity | Control sample0.0s below resolution against predeclared0.5s limit | Bounded observation, not instantaneous response or throughput guarantee |
| Cost | Three earlier model calls, reported USD0.0520185, reserved USD0.175104 against6calls/USD0.50 | No new calls in backup/rebuild/handoff; no price projection |
| Recovery objective | Last fully drained backup, no hard time ceiling; infrastructure10.563s | Later owner/catalog verification is separate; no end-to-end RTO or host-loss claim |
| Restored catalog | Initially237/237; after new fixtures337/337, zero pending reservations | Exact bytes/references, not scientific validity |
| Independent tool rebuild | Evaluator0.4/image95725806…; run `3cb8621ad9d54f5086727ef183ec3884` | Separate campaign from original live-model integration |
| Failure policy | Corrupt/missing/schema-mismatched backup rejected; old fence rejected; wrong policy identity blocked | Does not repair intermittent worker exit2/exit3 |

Current handoff checker is Deployment0.15. Original serving owners remain
Runtime0.65, Planning0.102, Research0.40, Knowledge0.18, Registry0.1, Data0.30;
Data0.31 is the separate compatible recovery auditor. Original and reconstructed
tool versions remain separately pinned. Original accepted Deployment0.14 wheel
evidence is not rewritten to0.15. Final0.15 qualification passed391 independent tests; see Acceptance_Qualification.json.

## Named successors and triggers

- [LR-01 Local Worker Reliability](../Build%20Plans/LR-01%20Local%20Worker%20Reliability.md): bounded actual-write diagnosis/repair; queued0%. No unattended reliability claim until qualified.
- [SQ-01 Scientific Quality and Iteration Views](../Build%20Plans/Completed/SQ-01%20Scientific%20Quality%20and%20Iteration%20Views.md): existing queued human/AI review of weak/questionable points between campaigns.
- SC-01 Scientific Source and Domain Qualification: not activated; requires selected scientific corpus/tool/assay and scientific acceptance criteria. Synthetic success cannot substitute. Source/domain selection remains owner input when this work is selected.
- PH-01 Production Host Hardening: not activated; trigger is an explicit production or remote-access requirement. Owns authentication/exposure, secret operations, operational recovery objectives and production observability.
- CP-01 Capacity and Cluster Qualification: not activated; trigger is a selected target/load and deployment profile. K3s replication, multi-campaign capacity and accelerators remain unqualified.

These are successor boundaries, not permission to expand closed BP-09 gates. The
[operator instructions](../../deploy/local/OPERATIONS.md) preserve independent
installation, diagnosis, drain, isolated restore and next-campaign replacement.
