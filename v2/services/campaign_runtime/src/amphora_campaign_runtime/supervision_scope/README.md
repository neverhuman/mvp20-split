# Runtime supervision scope

- Owner: Campaign Runtime, BP-07.04/B1.01. Runtime0.21 pure boundary;26 scoped tests cover119 statements/16 branches,100%; 111 independently installed scope/contract cases pass;162 predecessor production/migration files unchanged.
- Architecture: [Graph Runner](../../../../../docs/Architecture/System/Graph_Runner.md).
- Design: [Supervisor physical design](../../../../../docs/Build%20Plans/BP-07/BP-07.04%20Physical%20design.md).

NodeObservation owns an exact concrete ActivationPath/view and canonical state/output bytes, with a1MiB combined limit. It recomputes the existing plan-derived activation identity; it does not prove that the node exists in a retained plan. Its fingerprint includes status, reason, state and outputs. Captured dictionaries cannot mutate the retained observation. Non-JSON/coerced keys, nonfinite numbers and noncanonical byte readback reject.

DecisionFootprint groups original GraphReadCut provenance,1..64 exact Invoke targets and1..256 selected node observations under an8MiB payload ceiling. Targets must be present, unique and waiting/ready. The eventual Runtime transaction must additionally verify authenticated scope, stored plan/node membership, ancestry and absence of a materialized worker row. This pure record cannot confer permission or reserve work.

Footprint identity binds tenant/project/run/plan and sorted target/read identities. Relevant fingerprint additionally binds each complete selected observation. Both exclude global cut counters; original cut remains retained separately. It is not Planning's decision_scope declaration digest. Loop/scatter occurrences and scatter membership participate through the existing ActivationAddress profile.

Two footprints conflict when either one's targets intersect the other's selected reads (including targets), within the same scoped run. Shared reads alone do not conflict. A same-run plan mismatch rejects; separate runs/scopes are disjoint. Compare reports exact missing/changed selected nodes; unrelated supplied records and higher global revisions alone do not make it stale. Wrong-run/plan/scope or older cuts reject. Caller observations remain data until Runtime rederives them under its transaction.

No SQL, HTTP, provider dispatch, migration, mutable runtime state, accepted decision, policy grant or source-rights lease is owned here. Scientific quality and current graph-head selection are not inferred. Pinned domain receipts remain unchanged by future-only corrections. B1.02 public contracts and B2 admission/checkpoint/winner integration remain pending.

Tests live in tests/supervision_scope. Replacement preserves deterministic identities, bounded canonical observations, conflict symmetry, selected staleness and explicit failures. [Evidence](../../../../../docs/Audits/Evidence/BP-07-Supervisor/Scope_Boundary.json) records scoped coverage, independent installation and unchanged predecessor payloads. Unit policy is not concurrency evidence.
