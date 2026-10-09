# Campaign launch wire boundary

UI-01.06 approved2026-10-09. Contract0.1 owns strict launch request/profile/receipt
DTOs and deterministic envelope validation. Deployment owns lifecycle, grants,
profiles and private state. Runtime alone admits and executes the graph.

POST /v1/campaign-launches accepts the existing amphora-command-v2 envelope with
family campaign.launch and payload(profile, admission). Admission is a complete
existing graph.admit_draft envelope; its own legacy/numeric encoding remains intact.
Both identities must share scope, actor and command_id. This makes browser retries
and recovery refer to the same Runtime command, without a second derived identity.
The full request is bounded by the shared262144-byte/64-level command profile;
duplicate keys, nonfinite/unsafe numbers, unknown fields and coercion are rejected.

GET /v1/campaign-launches/{request_id} reads a scoped receipt. Profile catalog
publishes only pinned capability/image references and limits, never host paths,
credentials, executable commands or arbitrary worker options. Numeric values do
not inherit scientific validity from schema validation. Unknown admission outcomes
are not rejection. Released describes worker quiescence, not scientific success.

Public roots: LaunchRequest, LaunchReceipt, LaunchProfileCatalog. Consumers import
only this package root. Tests live in tests/contracts; lifecycle/replay/HTTP tests
belong to Deployment. Parsing normalizes the outer envelope and separately preserves
the existing Runtime command profile/hash. Authentication is not parser authority.
