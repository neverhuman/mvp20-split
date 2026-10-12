# Managed successor launch

Status: P4.1 implementation under qualification. Owner: Deployment. UI-01.08.

This additive module owns exact successor intent, predecessor-aware receipt projection
and authenticated HTTP intake/read/query. Public records come from the independently
versioned campaign-successor-launch contract. The shared campaign_launch lifecycle
owns the single installation slot, durable journal, preflight, recovery and workers.
There is no second supervisor, independent active slot or fresh-admission fallback.

The command preserves the full existing Runtime graph.admit_draft_successor bytes,
including exact predecessor cut, selected draft, carried-source expectations and
new inputs. Runtime alone accepts transfer and execution. Deployment never edits
predecessor records or reads Runtime tables. Request IDs remain scoped by family.

The existing loopback LaunchServer authenticates the installation actor/scope before
serving POST /v1/campaign-successor-launches, GET /{request_id} and POST /receipts/query.
Query binds full identity and original request digest. No paths, provider settings,
shell operations or process control enter browser requests. Recovery reuses original
admission receipts and immutable run bindings. Unknown outcomes keep the slot reserved.

Private launches.sqlite3 upgrades transactionally from its legacy eight-column shape
to add command family. It validates legacy canonical records and index metadata
before migration, copies original blobs unchanged, and preserves one UNIQUE active
slot across both families. Backups require both families drained. Do not open a
current journal using an older Deployment binary after cutover.

Tests: deploy/local/tests/campaign_launch/successor, plus original launch regression.
Qualification requires independent installation and actual owner integration; scripted
HTTP peers do not establish production worker or scientific correctness. P5 owns
live demo cutover. Module replacement must preserve original bytes, migration rollback,
family isolation, lost-reply recovery, original worker binding and drained release.
