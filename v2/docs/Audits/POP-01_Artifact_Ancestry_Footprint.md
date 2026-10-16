# POP-01.08 artifact ancestry footprint qualification

- Status: approved boundary implemented/qualified; no unresolved scoped drift.
- Reviewed: 2026-10-15 22:24:00 America/Chicago.
- Owner: Data0.33 / artifact_ancestry0.1; Search0.24 consumer, POP-01.01/E2.3.
- Decision: [POP-01.08](../Build%20Plans/POP-01.08%20Artifact%20ancestry%20footprint%20decision.md).

## Result and boundary

The approved scoped GET returns the exact root, distinct conversion-plus-derivation
identity count including root, checked catalog content-byte sum and existing
protected-closure membership digest. Existing read grant only. One read-only
repeatable-read transaction reuses Data's authoritative128-parent/4096-identity
traversal, catalog binding and cycle checks. No migration, command/audit writes,
payload storage I/O, processing grant, reservation or execution authority.

Root absence/scoped-away identity returns404; invalid/incomplete/oversized lineage
or byte overflow409; existing401/403/503 authority/storage failures remain safe.
Responses are bounded and no-store, including errors. The header adapter passes
legacy ASGI calls through unchanged; it does not buffer upload streams or change
cancellation. Counts describe a catalog observation, not a durable snapshot/lease.

Search SourceFootprints verifies exact scoped reference metadata, deduplicates
root identities before GET, rejects every unavailable/invalid/mismatched response,
and never infers a leaf from404. Source counts plus future successful publications
must fit4096 INCLUDING the future root. Content upper bounds include external
content plus all-attempt publications/binding budgets. Shared ancestors across
different roots may be double-counted conservatively. Digest refresh changes
require reassessment; authoritative Data completion/protection checks remain.
This component does not complete history/binding I/O or authored material composition.

## Evidence

| Gate | Result |
| --- | --- |
| New public contract | 9 source /9 independently installed pass |
| Full Data source PostgreSQL | 610 pass,32 optional Qdrant cases skipped |
| Installed Data ancestry/retention/derivation/rights SQL | 88 pass |
| Source Search | 481 pass; one sparse frozen-workspace check excluded as before |
| Independently installed Search | 479 pass; no peer implementations/SQLAlchemy/FastAPI |
| Focused composition | 95 pass |
| Boundary/schema checks | 46 pass;752 published schemas,750 predecessor bytes unchanged |
| Expanded isolation | All25 other service/tool/deployment implementation imports absent in each owner environment |

Data source SQL final: `.test-results/pop01-ancestry-sql-20261015d`.
Data installed final: `.test-results/pop01-ancestry-data-install-20261015b`;
SQL evidence `.test-results/pop01-ancestry-installed-sql-20261015c`.
Read-only public-contract client: `.test-results/pop01-ancestry-client-install-20261015a`.
Search final: `.test-results/pop01-source-footprint-search-install-20261015a`.

Actual HTTP `.test-results/pop01-ancestry-http-20261015a`: independently installed
Data plus contract-only read principal inspect a26-member derived closure and an
ordinary leaf, agree with retained membership digest and reconstruct identical
responses after Data restart. Retention inspection remains403.
`.test-results/pop01-source-footprint-http-20261015a` repeats this through isolated
Search's public SDK client and resource assessor, including explicit refresh.
No Data implementation is installed in that client. Both drivers exit0 and remove
their owned containers in finally; volumes and original demo remain.

SQL cases cover mixed conversion/derivation, shared ancestry, exact4096 membership,
checked byte overflow, scope/grants, missing/invalid lineage, no payload reads or
writes, no-store failures, later conversion registration changing the digest and
metadata remaining inspectable after processing rights are revoked. Existing
processing-content reads still deny that revoked use. No scientific-validity claim.

## Repairs and scoped drift review

Initial BaseHTTPMiddleware header handling changed legacy cancellation/process-loss
behavior. Full source b exposed four failures (606 pass/32 skip). Replaced it with
targeted ASGI pass-through; scoped recovery c29 and final full d610 pass. No old
stream/receipt semantics were relaxed. A stale representation migration test pinned
0012 although the previously qualified retention migration is0013; corrected that
test pin, with no new or regenerated migration. Existing read-state preservation
assertions remain. Data install a preceded the repair; final b supersedes it.

Installed SQL trials a/b failed test packaging, not service semantics: first the
isolated helper search path, then omitted public config.example.json. Explicit
pytest.ini/helpers and copied public fixture repair final c88. All trial containers
were removed. The curation schema-history test now excludes the independently
published ancestry family while still checking every predecessor digest; no pins
were regenerated or predecessor bytes changed.

Design/public contract/module implementation and public observation authority align.
Remaining resource/composition work stays POP-01.01/E2.3; E2.3/E2.4 remain0, E2=50%,
Execution37.5%, parent12.5%, Build18.75%, Verification0. E1/E2.1/E2.2 retain completed
credit. RG-01 remains after whole POP-01, before ML-01.

The owner also requested historical Docker cleanup. Removed13 verified exited
Amphora containers, preserving every volume and running demo pair. Evidence:
`.test-results/docker-stale-cleanup-20261015.json`. All new qualification containers
are removed; only the original PostgreSQL/Qdrant pair remains. No provider calls,
fleet work, original source changes, promotion or service restarts occurred.
