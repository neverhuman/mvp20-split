# Successor launch transport

Status: implemented; UI-01.08 P4.3b. Owner: Studio transport.

SuccessorSubmission retains one immutable numeric-profile outer command and nested
graph.admit_draft_successor request. It validates published schemas, same actor/scope/
request ID, exact predecessor, unique carry targets and artifact scopes. Decimal
graph input values are contract-defined strings and never converted to JS floats.
Shared command_wire preserves existing authoring wire behavior; canonical DTO
normalization and hashes remain Python owner responsibilities.

SuccessorClient only calls same-origin authenticated Deployment successor routes.
Explicit submit posts original bytes; receipt recovery with no observed owner hash
uses the approved GET by original identity. After a receipt is observed, the exact
identity/hash query checks that same owner command. This is an authenticated owner
read, not a browser proof of Python canonical hashing. Query responses must preserve
the original hash and all prior immutable receipt/admission bindings.

No direct Runtime admission, fresh-launch fallback, provider calls or implicit
retry. Missing, denied, conflict, busy, invalid and unavailable states are distinct.
Requests/replies are bounded; cancellation fences late replies. Terminal admission
cannot change, predecessor cannot become successor, and run links require a matching
accepted Runtime receipt. Deployment readiness is not execution completion.

Replacement tests: tests/transport/successor_launch. Public Python parser roundtrip
and actual owner/process/browser qualification remain separate acceptance evidence.

SuccessorSources reads only the bounded public Runtime carry-sources endpoint for
committed run exports. It authenticates through Gateway, validates the schema/run
and fences cancellation; no activation discovery or value payload is inferred.
Tests: sources.test.ts.
