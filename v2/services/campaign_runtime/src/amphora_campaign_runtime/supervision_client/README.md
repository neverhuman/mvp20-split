# Runtime-owned Planning client

Runtime0.33 adds CheckpointPlanningClient with the explicit v2 command family, CheckpointRequest model and /v2 routes. Original PlanningClient stays v1-only and rejects new commands before network I/O. Both share the existing bounded transport; no automatic repost, version fallback or provider call. Owned socket tests prove exact three-call submit/receipt/readback and lost-v2-reply recovery; client34 statements100%. Full API/client gate45 cases passed. Actual installed v2 owner exchange passed B2.01b.iv; evidence below.

- Current integration: B1.04d actual installed owner/restart proof passed; autonomous orchestration and decision effects remain B2.

- Version: Runtime0.29.0; reviewed `2026-10-05 16:04:54` (America/Chicago); BP-07.04/B1.04c.i.

PlanningClient(actor_id,scope,endpoint,token) accepts only exact numeric-v2 planning.supervision.request commands with the configured actor/scope. submit(command,window,guard=...) performs one effectful POST. receipt(command,window,previous=...) performs a read-only POST with the complete original command. readback(command,observation,window) performs one exact request GET. No method automatically calls another, retries, changes command identity, issues a provider call or accepts a graph decision.

ExchangeWindow bounds an explicit sequence to10s,3calls,524288 combined response bytes and262144 bytes per response. Connection/socket waits are at most5s; socket-shutdown timer bounds trickled headers/bodies. Explicit loopback HTTP origin/port only, printable32..512-character bearer, configured actor/scope, no proxy, redirects, credential logging or model URL. Strict JSON rejects duplicate/nonfinite metadata; no compressed responses. Transport reuses only Runtime-owned strict JSON helpers; no Planning-private import or peer SQL.

Writes require a callable guard before connect and immediately before send. Caller owns durable lease/current authority; a callable is not proof of eligibility or a provider grant. Transport runs outside SQL. Unavailable/lost reply means uncertain write, not evidence it failed. ExchangeDenied, ExchangeAbsent (including receipt-query404), ExchangeConflict and ExchangeInvalid remain distinct. A write404 is unavailable, not proof of no commit. Preserve original intent for receipt recovery.

SupervisionReceiptObservation validates original full command identity/hash, stable owner operation, exact typed commit and original readback. Recorded receipts remain awaiting_readback until exact owner data is verified. Previous terminal receipts cannot change. No scientific or execution authority follows from recording success.

Tests/supervision_client uses actual loopback HTTP peers for exact wire/auth/routes, lost replies without resend, malformed/altered receipts, changed operations/readbacks, guards, read-status distinctions, byte/deadline limits and invalid configuration.64 client/receipt cases5.61s;12 boundary8.44s.146 statements30 branches94%; socket-expiry cleanup, write404, empty read and already-expired-window branches not all directly reached. Actual installed Planning owner is verified under B1.04d; durable autonomous orchestration remains B2. Replacement must preserve method separation, exact bytes, bounds, failure distinctions and no automatic retry.


B1.04d actual-owner proof verified 2026-10-05 16:32:49: independently installed Runtime0.29/Planning0.72/Data0.29;11 process stages,6 owner hosts,2 commit-before-reply-drop losses. Exact original receipts/readbacks and Runtime capture/commit timestamps survive replacement; current Data process withdrawal blocks fresh response while original receipt replay remains available; explicit regrant permits new submission. Cancellation remains history and Planning attempts remain zero. Probe cleanup closes hosts/proxies and cancels only its unique run. Evidence: docs/Audits/Evidence/BP-07-Supervisor/Actual_Owners.json. Autonomous delivery/decision winners remain B2.


B2.01b.iv installed verification: both profiles remain compatible in four isolated owners668 cases; actual v2 materialization request, two commit-before-reply losses, six owner hosts and replacement/rights replay passed. Checkpoint_Owners.json owns evidence. No automatic graph checkpoint or winner yet.
