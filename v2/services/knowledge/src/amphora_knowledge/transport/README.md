# Knowledge HTTP and host boundary

BP-06.02/B1 implementation. Design: [authoring](../../../../../docs/Architecture/Knowledge/Authoring.md). This module composes private Knowledge behavior and public Data/Research clients; it owns no peer state or scientific authority.

The explicit host serves on `127.0.0.1` using FastAPI/Uvicorn, with at most16 concurrent connections. Run `python -m amphora_knowledge check --config <file>` or `serve --config <file> --port 8085`. Importing packages creates no connections. Startup requires the previously migrated `knowledge_service` role, verifies owner-table access and does not migrate or probe peers. Operators apply migrations separately with `knowledge_migrator`.

Configuration is bounded strict JSON (512 KiB), with exact keys `database_url_env`, `principals`, `vocabulary`, `policy`, `data`, `research`. Principals contain `token_env`, `actor_id`, `scope`, `actions`; grants are nonempty subsets of `read_graph`/`propose_graph`. Tokens and database URLs are environment references, never inline configuration values. Data/Research entries contain `endpoint` and `token_env`; each is an explicit loopback HTTP endpoint. Data credentials need `read` and `source_history`; Research credentials need `read_declarations`. Each peer's scoped credential must match the submitted graph's tenant/project. Incorrect configuration cannot grant cross-owner authority.

`vocabulary` is a public DomainVocabulary; `policy` is the exact definition from StructuralPolicy.definition(), with synthetic structural authority and explicit history caps. Defaults apply only when first intent pins a new graph profile. Existing profiles are immutable; changing process configuration does not migrate them. Profile discovery before first intent is an observation, not a reservation.

| Method/path | Request | Result/authority |
|---|---|---|
| GET /health | none | Static owner/structural authority; no peer readiness claim |
| POST /v1/graph-proposals | GraphChangeProposal | Durable GraphChangeDecision; actor bound to authenticated principal |
| GET /v1/graphs/{graph_id}/proposals/{change_id} | Path identifiers; credential scope | GraphProposalStatus; null decision means pending |
| POST /v1/graph-profiles/read | DomainGraphRef | GraphAuthoringProfile; configured_default or stored |
| POST /v1/graph-heads/read | DomainGraphRef | Exact DomainHead |
| POST /v1/graph-snapshots/read | DomainRevisionRef | Exact immutable DomainGraphSnapshot |
| POST /v1/graph-changes/read | AcceptedChangeRef | Exact immutable AcceptedGraphChange |

All graph routes require bearer authentication and scoped grants. Request parsing has a 256 KiB/5-second bound and rejects duplicate keys, nonfinite JSON, extra fields and caller-injected actor/validation authority. Responses use no-store. Proposal responses return200 for completed accepted/rejected/conflict decisions; clients must inspect the outcome. Changed same-ID content returns409. Unknown exact records return404; scope/action denial403; missing/invalid credentials401; malformed requests422; body limit413; body deadline408; wrong media415. Peer outage/protocol ambiguity returns503 with pending intent; SQL failure returns503 and clients reconcile before retry. A dropped HTTP connection is not evidence that an in-flight transaction was cancelled.

The accepted change links to its base head; clients can traverse immutable prior revisions using exact read requests rather than relying on a mutable offset listing. Profile reads compute the canonical vocabulary hash and return the graph's pinned policy reference. Snapshot/change reads verify stored hashes/identity before returning success. No generic query, private SQL interface or graph mutation by GET exists.

Tests live in `tests/api`: real PostgreSQL plus in-process ASGI verifies credentials/scope, profile pinning, proposal/receipt replay, immutable reads, malformed inputs and pending recovery using scripted peers. Host configuration tests include a separate process `check`. The separate tests/acceptance suite proves actual three-owner HTTP, Knowledge process restart, Research outage/recovery and current-rights rejection. Independent wheel replacement and mid-build interruption remain subsequent proofs; do not infer them from TestClient.
