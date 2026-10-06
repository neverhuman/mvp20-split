# Checkpoint report disposition

OutcomeResolver owns run-locked interpretation of retained Planning execution reports. Existing WinnerStore.resolve_locked composes the original winner transaction: committed winner first, run cancellation, original deadline/eligibility fallback, otherwise current policy/footprint/scalar acceptance. No peer I/O occurs in resolution.

Absent report or required exact response stays pending. Successful reports require the same observation hash from Runtime's already-authorized capture/response journal, then use existing ModelWinner checks. Known model-policy/value/staleness failures create a repair intent; integrity and unexpected errors propagate. Invalid output and policy rejection need exact retained response evidence. Context/configuration/budget stops and uncertain/unavailable exhausted providers choose the pinned fallback. Weak scientific confidence alone is not a failure reason.

Runtime0028 retains one immutable request disposition, attributed to report and optional response hashes, with SELECT/INSERT-only grants and original replay. Fallback disposition and winner/audit/outbox commit together. Repair consumes no new call itself; the later bridge must atomically prepare/reserve its child. Existing actual request/call reservations bound repair; legacy policy without recipe cannot acquire autonomous repair authority. No refunds. Deadline/winner precedence survives replacement.

ModelWinner now also rejects superseded request ordinals and requires a retained execution report's exact observation when present. Late different captures remain diagnostics. Old committed winner replay precedes these current checks.

Tests in tests/supervision_resolution use actual Runtime PostgreSQL, admitted recipe/reservations and scripted Artifact publication/public model responses. This does not prove an installed Planning model or automatic scheduling. c.ii.3c owns preparation/error bridge, c.ii.4 scheduling, B3 independent process races and V1 installed integration. Preserve immutable request/report/disposition/winner history and transaction ordering when replacing this module.

Verification:52 combined cases58.69s,22 final32.90s. Resolution131statements34branches96%; remaining paths are unrelated-attempt skip, unexpected response-binding propagation, legacy-policy no-repair allowance and no-response disposition restoration. Winner module225statements26branches100%. Initial tests used Invoke fixture for a scalar adjustment; corrected to an actually admitted scalar recipe/reservations. No production validator was weakened.
