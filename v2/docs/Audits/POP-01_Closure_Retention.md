# POP-01 closure retention prerequisite

- Qualified: 2026-10-15 11:48:49 America/Chicago; POP-01.01/E2.2a, approved POP-01.06.
- Scope: Data0.32/artifact_0013 and Runtime0.69/runtime0029. Population workers,
  authored collection and the full batch/cap matrix remain E2.2-E2.4.
- Worktree: pop01-retention-integration based on afe121c0. Original review checkout
  stays frozen; promotion waits for owner review completion and wrapper drain.

Data owns bounded immutable derivation/conversion closure membership. One existing
root reservation/proof governs all members. Runtime explicitly pins the profile in
new graph runs and stores its membership receipt atomically alongside the existing
root receipt. Ordinary history remains direct-root. Unknown profiles, incompatible
owner support and missing closure proof cannot authorize execution acceptance.
No worker command/DTO, old schema, execution counter or Runtime route changed.

## Verification

- Data96 actual SQL owner checks: nested/shared ancestry, scope/digest, cycles,
  atomic rejection, immutable membership, root proof transitions and shared protection.
  Evidence .test-results/pop01-closure-sql-7acb4206/pytest.log.
- Runtime181 completion/lifecycle/scheduling SQL checks pass; six focused final
  checks also pass, including two additional root-only and companion-write rollback
  cases. Evidence pop01-closure-sql-48533c14 and pop01-closure-sql-91175f6b.
- Public schema publication32 plus test ownership4 pass; production dependency
  guard passes. All748 published schemas retain744 predecessor byte pins.
- Independently built Data and Runtime wheels exclude each other's implementation.
  Manifests .test-results/pop01-closure-owners-20261015b/<package>/manifest.json.
- Actual installed authenticated HTTP proof: pop01-closure-http-20261015d/evidence.json.
  Diamond ancestry has four distinct members. A successful Data reservation response
  is lost; Runtime remains prepared. Both owners restart; the identical completion
  retries the original reservation and commits. Actual Runtime proof confirms the
  entire group; readback retains count/digest. A second lost-response run cancels;
  actual aborted proof releases that group while the independently confirmed group
  stays confirmed. No provider calls or scientific execution.
- Every new fixture container and probe subprocess removed; labeled volumes/evidence
  retained. Existing review databases and source untouched.

The harness uses a separately hash-pinned synthetic descriptor with300-second restart
bounds. This proves protocol/replacement behavior, not scientific validity, populated
campaign execution, throughput or an unrestricted4096-artifact expansion guarantee.

## Compatibility and return point

New host configuration requires the paired retention profile and closure endpoint;
read-only authenticated route and migration readiness checks precede startup/fresh
admission. Original terminal replay precedes availability checks. Legacy snapshots
stay unprofiled. Root receipt format and existing confirmation/reconciliation remain
unchanged. Drain profiled work before downgrade; current-owner resource-preflight
with target release rejects active closure profiles below0.69.

The fixture readiness probe now targets final TCP PostgreSQL, avoiding initdb's
transient socket-only server. This repairs verification tooling, not production
service policy. Review source remains frozen in the original checkout.

E2 remains25%, Execution31.25%, parent10.42%, Build15.63%, Verification0. This closes
the retention prerequisite inside the unfinished E2.2 worker unit, not the whole unit.
Next: implement population step workers and declared ancestry behind approved public
population_steps; then authored composition and the actual batch/cap matrix. RG-01
remains immediately after POP-01.
