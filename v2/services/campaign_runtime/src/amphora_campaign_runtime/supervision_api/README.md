# Runtime supervisor recording API

- Current integration: BP-07.04 closeout; Runtime0.60/runtime0028, reviewed `2026-10-06 03:23:38` (America/Chicago).
- Owner: Runtime response/cancellation recording and authoritative decision readback. Winner mutation remains the separate Runtime winner/resolution boundary.

## Boundary and ordering

SupervisorRecording owns incoming response/cancellation recording and readback, plus scoped readback of committed CheckpointDecision records. For response POST: require original command actor/scope and supervise_respond, reconcile original stored receipt (including exact bytes/hash for pending commands), load original request and verify original Planning actor, response reference, attempt engagement/hash and capture scope, then fetch fresh Data processing-content if needed, and record through ResponseJournal. SQL transactions do not span Data I/O. A committed receipt returns before any new Data access; fresh requests still require current Data authorization. read is required for receipt reconciliation. Historical GET/query needs read only; it never grants a fresh response. Empty diagnostic responses require no Data. Missing capture reader fails503 for nonempty captures.

CancellationJournal owns cancellation checks and atomic history/receipt recording; API success means recorded history, not execution cancellation. Neither route issues provider calls, changes graph topology, edits pinned evidence, creates a decision winner or refunds unknown usage.

## Public HTTP and host configuration

Existing Runtime create_app gains optional supervision=SupervisorRecording; requires configured lifecycle and credentials. Existing default app has no supervisor routes. All routes reuse Runtime body262KiB/10s/depth64 middleware and configured bearer principals. SQL/network work is thread-offloaded. OpenAPI documents bearer security. Unknown query parameters fail422; body/errors are redacted. Authorization401/403, missing history404, changed commands409, invalid binding422, unavailable capture/persistence503. Data processing denial403 is explicit.

POST /v1/supervision/responses and /v1/supervision/cancellations accept original numeric-v2 respond/cancel commands. Each has /receipts/query appended for read-only POST lookup using the complete original command. GET /v1/supervision/responses/{response_id} and /v1/supervision/cancellations/{cancellation_id} return exact public records. GET /v1/supervision/ready checks owned request/response/cancellation tables and reports supervisor_recording_only. Normal Runtime readiness remains compatible.

Host JSON opts in with supervision:{} for diagnostics/cancellations, or supervision:{capture_data:{endpoint,token_env}} for configured Data capture reads. Secrets remain in the named environment variable. Host checks readiness and never migrates. Configured actions now include supervise_respond and supervise_cancel; read supports original receipt/history. This host constructs RequestJournal with no producer mapping: original request preparation and autonomous orchestration remain B2, not an incoming HTTP capability. Runtime0.28 requires existing0020; NEVER run Runtime<=0.26 migrators against it.

## Replacement and verification

Keep routes, original command profiles/identities, receipt-before-fetch order, actor/scope checks, redaction, opt-in activation and no execution effects. Existing legacy Runtime API/host tests remain applicable. tests/supervision_api owns actualSQL/API tests with deterministic capture-failure probes; exact Data wire protocol is independently tested in supervision_capture.21 scoped API/response/cancellation/legacy host/body cases15.77s;12 boundary checks10.41s.116 statements8 branches99%, only capture-less Host configuration branch not directly exercised. B1.04d installed multi-owner restart/lost-reply evidence is verified below; live model calls remain separately gated.


B1.04d actual-owner proof verified 2026-10-05 16:32:49: independently installed Runtime0.29/Planning0.72/Data0.29;11 process stages,6 owner hosts,2 commit-before-reply-drop losses. Exact original receipts/readbacks and Runtime capture/commit timestamps survive replacement; current Data process withdrawal blocks fresh response while original receipt replay remains available; explicit regrant permits new submission. Cancellation remains history and Planning attempts remain zero. Probe cleanup closes hosts/proxies and cancels only its unique run. Evidence: docs/Audits/Evidence/BP-07-Supervisor/Actual_Owners.json. That historical recording-only proof is complemented by the subsequently verified autonomous owner proof; see supervision_loop/README.md.

## Authoritative decision inspection

GET /v1/supervision/decisions/{run_id}/{decision_id} returns the existing CheckpointDecision contract through WinnerStore, scoped from the authenticated principal and requiring read only. Pending, unknown and foreign-scope identities return the same unavailable404. Reading never resolves a checkpoint, issues work or accesses Data/Planning. A recorded response remains a proposal until Runtime commits a winner. Accepted, fallback and cancelled outcomes preserve their exact reason/effect and original pins. The ready route retains its existing recording-only compatibility label; it is not a declaration of campaign progress.

Verification:40 actual SQL/API/winner/resolution cases passed56.66s;12 boundaries passed12.25s; schema publication unchanged. Four actual HTTP reads from isolated Runtime0.60 processes preserve earlier accepted/fallback decisions across replacement on fresh loopback ports; no migration or peer availability required. See Checkpoint_Decision_Read.json under docs/Audits/Evidence/BP-07-Supervisor. API replacement also covers cancelled decisions in the SQL suite. Listing, full engagement lineage and context omission UI belong to BP-07.05; this exact read is not that discovery surface. No aggregate coverage percentage is claimed for this delta.
