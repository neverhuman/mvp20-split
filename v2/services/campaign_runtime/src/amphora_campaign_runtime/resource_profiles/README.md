# Runtime resource profiles

Owner: [Runtime architecture](../../../../../Architecture.md), approved POP-01.05.
`InvocationCapacity` validates the explicit immutable admission snapshot, exposing
capacity against the existing run reservation ledger. Legacy snapshots select no
capacity; unknown profiles or invalid bounds fail closed. No process configuration
can add a limit to a historical run.

GraphAdmission accepts the new numeric `graph.admit_draft_bounded` command through
`POST /v1/graph-drafts/admit-bounded`, using ordinary draft/universe/Registry checks
and the same guarded single-run transaction. The complete request is retained in
`runtime.runs.input_snapshot`; no extra tables or mutable counters are introduced.

RuntimeLeases loads capacity after locking the run and replaying existing receipts.
For bounded runs it settles expired attempts across all tools before claim selection.
Prepared completions and uncertain attempts keep their reservations. Existing
ActivationState settlement rules determine retry eligibility and side-effect
uncertainty. No Artifact I/O occurs while locks are held. Capacity exhaustion returns
the existing no-work receipt, with no extra issuance or fencing changes. A fresh
command is needed to poll again. Physical remote process termination is not owned here.

Actual SQL concurrency/recovery and installed restart qualification belong to
Runtime tests; DTO/schema byte stability belongs to campaign_resources and Dev.
Host.load rejects unsupported profiles in running or unsettled runs before serving
or coordinating. The read-only owner CLI `resource-preflight --config ...
--target-release ...` rejects pre-0.68 targets while bounded work is active. Terminal
settled history remains readable independently. Deployment must invoke this owner
preflight rather than reading Runtime tables. Preflight integration and installed
restart qualification are required before this phase can close.

Runtime0.69 also checks the immutable artifact-retention pin in active/unsettled
run tool snapshots. Current-owner preflight with an explicit target release rejects
pre-0.69 targets while a closure-profile run is active. Host startup requires its
configured supported Data peer. [Completion](../completion/README.md) owns the
profile's transport, companion proof and compatibility/recovery details.
