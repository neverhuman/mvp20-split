# Curation compiler handoff

UI-01.08/P2.3c.2. Reuses original CompilerSelection slot, store, journal and
CompilerProgression; no new API, table, graph encoder or Runtime admission.
Slot identity is unchanged: original actor+provider attempt, independent of output
and configuration. Exact selection replay survives loss between selection retention
and job progress. New selection inserts require an active curation fence before
writes and commit. Configuration changes conflict at the original slot.

The compiler receives the exact retained model graph after reviewed declaration,
input, budget, proposal and accounting reconstruction. No synthetic graph repair
or replacement. Existing current processing/eligibility checks and Runtime numeric
save/validation contracts remain authoritative. Each invocation advances one bounded
compiler step under the existing compiler lease. Job expiry does not physically
cancel an already delegated/issued compiler command; job progress still requires
the current job lease. Original command receipt reconciliation prevents duplicates.

Ready requires exact retained Runtime structurally-valid validation with original
draft/revision/content/validation/universe pins. Invalid compilation and rejected
commands remain failed; temporary blocked/pending work remains compiling with a
reason. A validated draft is not admitted, scientifically proven or source-authorized
for later execution. Original provider output and queued receipt remain immutable.
Tests: tests/curation_compiler; managed process/replacement acceptance remain later.

Verified:7 SQL/scripted-owner workflow cases,48 legacy selection/storage/boundary
checks and2 final persisted-attempt binding checks. Periodic production heartbeat
and independently installed owner replacement remain c.3/P2.4.
