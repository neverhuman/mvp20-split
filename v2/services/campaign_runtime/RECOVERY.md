# Foundation Recovery and Replacement

- Scope: BP-02 synthetic invocation foundation; single-server development/internal acceptance.
- Design boundary: runtime owns acceptance and attempt budgets; artifact service owns bytes and retention. General graph interpretation and scientific validity are separate capabilities.
- Verification owner: [installed acceptance](tests/acceptance/README.md); canonical progress remains the active build tracker.

## Retained State and Configuration

Preserve both service-owned PostgreSQL schemas and the artifact storage root together with the deployed package versions, explicit principal/scope configuration, pinned tool/fixture descriptors, runtime outcome endpoint, artifact reservation endpoint and stable inspection cursor key. Preserve command identities and immutable receipts when retrying. A historical successful claim does not grant new execution authority.

Ordinary startup uses only the restricted `runtime_service` or `artifact_service` database role. Each host receives only its own database URL and configured public peer tokens. HTTP tool workers receive no database credentials. Migrations are explicit owner operations; API startup never performs DDL.

Install each service wheel with its public contract dependencies in a separate environment. Run its `check --config <path>` command before serving. The configuration examples are independent synthetic profiles; match schema hashes, scope, trusted tool descriptors and public peer endpoints deliberately. Retain the existing storage root rather than initializing empty storage against an existing catalog.

For owner-authorized local migration, the packaged entrypoints are `python -m amphora_campaign_runtime.persistence.migrate` (environment key `AMPHORA_RUNTIME_MIGRATION_URL`) and `python -m amphora_data_artifacts.persistence.migrate` (`AMPHORA_ARTIFACT_MIGRATION_URL`). Supply that owner's migrator credential only to the bootstrap process. Never use the migration credential for normal hosting or workers.

## Recovery Order

1. Restart the artifact and runtime hosts against their retained owned state and matching configuration. `/ready` confirms database access; `/health` describes configured capability, not complete deployment health.
2. Observe the scoped run and original command receipts through runtime reads. Use current artifact reservation reads for current protection; replaying an old reserve command can legitimately return its historical reserved receipt.
3. Retry an interrupted completion with exactly its original command identity and payload. Durable PREPARED bindings protect artifacts while the coordinator resumes. A committed command returns its original receipt. Cancellation or revocation cannot be reversed by retry.
4. If stale prepared intents block reclaim, run bounded runtime `reconcile-intents --config <path> --actor <maintainer> --tenant <tenant> --project <project> --run <run> --limit 20`, following `--after` until the pass ends. This records exact abort proof and terminal command disposition. It does not guess peer absence means abort.
5. Run bounded `settle` for the same authorized run when required, then let eligible workers claim through the public API. The live database clock, current attempt and higher fence determine authority. An issued attempt is spent once; uncertainty retains its reservation and remains blocked.
6. Run runtime `deliver --config <path> --actor <delivery-principal> --tenant <tenant> --project <project> --limit 20 --time-budget 20`. Public delivery reads show pending, leased, acknowledged or exhausted operations. A killed delivery process is recovered after its stored lease expires; operation identity remains stable. Missing notification destinations fail/back off and eventually exhaust; they do not undo accepted execution. No automatic redrive resets exhausted evidence.
7. Artifact `reconcile` provides a bounded owner sweep using an explicitly configured retention principal. Only an exact committed or irreversible aborted runtime proof changes protection. Prepared, unknown, malformed and unavailable outcomes preserve it. `cleanup` affects eligible provisional attempts, not finalized accepted artifacts; stop older writer versions before enabling cleanup.

These are explicit bounded maintenance commands, not an implicit scheduler or a promise of automatic production recovery. A scheduler, target-host operating profile and operational RTO remain later gates.

## Independent Replacement Acceptance

The replacement gate installs fresh runtime and artifact environments outside the checkout from the tested wheels, terminates the original service processes, reapplies each owner's migrations idempotently through separate bootstrap credentials, and restarts retained state. It verifies exact original receipt/report, scoped run/budget, signed cursor continuation, accepted hash-matching bytes and still-protective reservations. Delivery from the replacement runtime then confirms the pending bindings without changing accepted history. Neither replacement contains the peer implementation or scientific packages.

`v2/dev/verify_foundation.py --builds` with `AMPHORA_TEST_POSTGRES=1` runs the component suites, independent installs and named REC-01..09 scenarios. Manifests are under ignored `v2/.test-results/recovery/<scope>/`, with exact public IDs, wheel hashes, barriers, owned killed PIDs, restart steps, deadlines and observations. Failed or incomplete scenarios cannot claim a pass. Test-only fault entrypoints are excluded from service wheels and cannot be enabled through normal configuration. Do not reset the fixture concurrently with these probes.

This proves application process recovery and replacement against retained local state. It does not prove host power-loss safety, filesystem/volume failure recovery, backup restoration, replicated deployment, target DGX/Threadripper operation or scientific correctness. BP-09 owns target-host durability and backup acceptance. Preserve this distinction when presenting the engine.
