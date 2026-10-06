# Planning supervisor HTTP boundary

Planning0.75 adds explicit POST /v2/supervision/requests, POST /v2/supervision/receipts/query and GET /v2/supervision/requests/{engagement_id} using CheckpointRequest and its distinct command family. Existing /v1 routes remain closed; reading a retained record through the wrong profile returns409. Both versions share bounded authenticated transport and existing grants. Readiness requires the planning0016 family constraint, not only table existence.45 combined API/host/client cases passed;24 owned API cases pass with path-based coverage: app96%, entire API87% (CLI subprocess is not instrumented). Unexecuted app lines: DBAPI error handler, one access classification and incompatible-schema readiness; these remain explicit gaps. No model attempt or execution authority.

- Current integration: B1.04d actual installed owner/restart proof passed; autonomous orchestration and decision effects remain B2.

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

Replacement must preserve original command bytes/profile/identity, bearer-to-principal selection, redacted bounded errors, read-only recovery and the absence of provider/execution effects. tests/supervision_api owns ASGI, actualSQL and separate CLI-host probes.39 combined API/intake cases pass (22 API,17 intake), including real HTTP request/receipt recovery;12 boundary checks pass. In-process coverage191 statements/50 branches86%; CLI subprocess lines are not included in that coverage and are tested separately. Untaken ASGI branches: persistence503, generic binding422 and second receive delegation. B1.04d separately installed multi-owner restart proof is verified below; autonomous orchestration remains B2.


B1.04d actual-owner proof verified 2026-10-05 16:32:49: independently installed Runtime0.29/Planning0.72/Data0.29;11 process stages,6 owner hosts,2 commit-before-reply-drop losses. Exact original receipts/readbacks and Runtime capture/commit timestamps survive replacement; current Data process withdrawal blocks fresh response while original receipt replay remains available; explicit regrant permits new submission. Cancellation remains history and Planning attempts remain zero. Probe cleanup closes hosts/proxies and cancels only its unique run. Evidence: docs/Audits/Evidence/BP-07-Supervisor/Actual_Owners.json. Autonomous delivery/decision winners remain B2.
