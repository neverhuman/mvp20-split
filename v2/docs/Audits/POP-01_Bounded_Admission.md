# POP-01 bounded admission milestone

- Reviewed: 2026-10-14 21:22:00 America/Chicago; working tree after 65710ea9/c1798191.
- Owner: POP-01.01/E2, first of four bounded delivery units. This is not E2 closeout.
- Contract: approved [POP-01.05](../Build%20Plans/POP-01.05%20Bounded%20graph%20admission%20decision.md).

Runtime0.68 implements the separate bounded draft admission command/route and
retains the complete immutable request. Claims select capacity from that snapshot
after locking the run and replaying receipts. Eligible expired reservations are
settled across tool types; prepared completion and uncertainty retain their slots.
Capacity1/4/8 saturation, exact replay, cross-tool expiry, failure, cancellation and
prepared-intent reconciliation pass against actual PostgreSQL transactions.

Host startup and graph advancement reject unsupported selected profiles. The
read-only resource-preflight CLI can assess a target release. Deployment0.20.3
invokes the public owner CLI before process launch; unavailable or older binaries
without this check are refused conservatively, even for legacy-only deployments.
Qualified Runtime still supports old admission families and history. Drain bounded
work before downgrade or roll forward; preflight does not terminate remote workers.

## Evidence and limits

- 243 source Runtime checks pass across definitions, lifecycle, completion,
  scheduling and API, using isolated PostgreSQL state.
- 21 checks pass from an independent Runtime installation with peer service
  implementations absent. Two actual HTTP serving processes preserve the same
  claim/no-work receipts and capacity after restart. Pre-0.68 target assessment
  rejects active bounded work.
- Independently installed Deployment accepts the qualified Runtime preflight and
  refuses the retained0.67 binary before launch. The test PostgreSQL container was
  recreated from its original labeled volume, preserving unsettled records.
- 79 final Deployment lifecycle/boundary/Runtime profile checks pass. Contract
  publication remains744 schemas,740 predecessor bytes pinned.
- Every newly created test container was removed in a finally block. Retained demo
  PostgreSQL/Qdrant and historical user/recovery data were untouched.

Evidence: ignored .test-results/pop01-capacity-sql-432e7fa0/pytest.log;
pop01-capacity-installed-de7b8b2d/pytest.log and deployment-preflight-evidence.json;
pop01-runtime-resource-install-a/manifest.json and
pop01-deployment-resource-install-a/manifest.json. Reproduction helpers are
verify_bounded_capacity_sql.py, verify_bounded_capacity_installed.py and
verify_bounded_deployment_preflight.py in .test-results. Tests themselves are owned
under Runtime definitions/lifecycle and Deployment lifecycle, with existing scopes.

No new reservation ledger, SQL migration, legacy admission schema or worker-wire
change. This proves generic capacity/recovery on the development host with Linux
PostgreSQL; it does not qualify production Linux hosting, full population dispatch,
scientific outcomes, nested heterogeneous method execution or throughput. Those
remain the subsequent E2 delivery units and E3/E4 gates.
