# Planning supervisor HTTP boundary

- Version: Planning0.71.0; public supervision0.2.0; SQL head0015.
- Reviewed: `2026-10-05 15:46:25` (America/Chicago).
- Owner: Agent Planning; implementation unit BP-07.04/B1.04b.i.

## Responsibility and authority

Expose authenticated original-request intake, immutable receipt recovery and exact request readback through the owned supervision_intake module. Runtime alone owns execution decisions. A recorded response means persistence, not model issuance, graph acceptance or scientific truth. No provider call, attempt, budget reservation, repair enrollment or peer SQL is performed.

## Public surface

Configured create_app(intake, credentials) exposes POST /v1/supervision/requests, POST /v1/supervision/receipts/query and GET /v1/supervision/requests/{engagement_id}. Both POST bodies are the original numeric-v2 planning.supervision.request command. Receipt queries are read-only and compare original full identity and SHA. Exact retries recover the original public receipt and commit time. Unknown history is404; changed command/query409; recorded logical conflicts are typed rejected receipts200. Existing Planning record_requests and read_attempts grants apply; caller bodies cannot grant authority.

Credentials accepts1..64 operator-configured token/principal pairs. Tokens are unique printable ASCII32..512 characters; bearer matching uses constant-time comparison. Configuration JSON has exact token,actor_id,scope,actions fields, max64KiB, strict duplicate/nonfinite rejection. Unknown actions fail existing Principal validation. Authentication401, authorization403, input422 and persistence503 errors are redacted; command/auth payloads are not echoed.

Whole-body middleware bounds cumulative bytes262144, total receive time10s and JSON depth64, including chunked bodies. Oversize413, timeout408, malformed/deep422. SQL work is thread-offloaded; the CLI configures a5s statement timeout. Unconfigured app exposes health only: /live succeeds, /ready503, no command routes. Configured readiness checks both owned intake tables. GET /ready and /live are operational probes, not proof of model readiness. OpenAPI carries bearer security.

## Deployment and replacement

Run amphora-planning (or python -m amphora_agent_planning.supervision_api), default127.0.0.1:8007; --host and --port are operator choices. AMPHORA_PLANNING_DATABASE_URL and AMPHORA_PLANNING_SUPERVISION_CREDENTIALS are environment-only configuration. Startup never migrates; install current0015 first and never run Planning<=0.69 migrators against it. Invalid startup configuration is redacted. Engine disposal occurs when the server returns; durable state is owned by supervision_intake, not this HTTP module. FastAPI/Uvicorn are declared private runtime dependencies; no private peer imports.

Replacement must preserve original command bytes/profile/identity, bearer-to-principal selection, redacted bounded errors, read-only recovery and the absence of provider/execution effects. tests/supervision_api owns ASGI, actualSQL and separate CLI-host probes.39 combined API/intake cases pass (22 API,17 intake), including real HTTP request/receipt recovery;12 boundary checks pass. In-process coverage191 statements/50 branches86%; CLI subprocess lines are not included in that coverage and are tested separately. Untaken ASGI branches: persistence503, generic binding422 and second receive delegation. Actual separately installed multi-owner restart proof remains B1.04d; autonomous orchestration remains B2.
