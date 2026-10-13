# Managed curation work

UI-01.08/P2.3c.3. Internal scheduling/lifecycle; no import-time startup or new API.
CurationDiscovery selects one scoped actor-owned, configured-policy job with a
bounded keyset query and wraparound. Terminal jobs and active leases are skipped;
discovery is only a hint, never claim/dispatch authority. Own Planning SQL only.

LeaseKeeper periodically renews an exact opaque job fence (default10s/60s lease),
refreshing current immutable progress under the job lock so a concurrent phase
transition does not falsely lose its heartbeat. Replaced or expired fences cannot
renew. Terminal progress is read without renewal. Graceful shutdown joins the
heartbeat and releases only its exact fence; a replaced worker cannot release a
successor. Background errors surface as bounded diagnostics, without SQL secrets.
No peer I/O is held under SQL. In-flight calls retain original issuance authority.

Current implementation: discovery/heartbeat/lifecycle/polling, configured process and independently installed replacement qualified. Tests owned by
 tests/curation_worker and curation_jobs. No model key, network call or startup
occurs through these primitives alone. Existing heartbeat strict-revision API
remains unchanged; refresh is the managed keeper's original-fence operation.

CurationWorker.tick claims one job, keeps its fence alive and advances one phase:
original declaration/public context and input freeze; original provider issuance/
result; or one existing compiler step. Recovery of retained input/declaration is
before current policy lookup. Original receipt/proposal remains immutable. Missing
provider stays pending; bounded budget/preparation/publication failures retain named
status. Typed transport uncertainty stays pending for original receipt recovery;
unexpected integrity/programming errors propagate. CLI/configuration is implemented below.

CurationPoller advances one selected job per turn, wraps its keyset cursor fairly,
checks a stop event between bounded turns and enforces finite polling deadlines.
No provider retry is authorized by another turn. Original-context timeouts pause;
active predecessor/denied sources fail before provider.36 worker/job tests pass.

## Private process boundary

Run `python -m amphora_agent_planning.curation_worker check --config <file>` for
Planning serving-role/table readiness. It does not claim work, read the provider
key or prove peer/provider availability. `run --seconds 20 --interval 1` enables
bounded turns; SIGINT/SIGTERM/SIGBREAK request drain after the current bounded turn.
No import-time startup, migration, shell execution or browser-controlled settings.

WorkerConfiguration is a private planning-curation-worker.v1 DTO: scoped actor,
worker ID, database environment reference,1..32 reviewed policy files, Data/Runtime/
Registry/Knowledge/Research endpoint and token references, Runtime owner and exact
Registry eligibility configuration. ReviewedConfiguration validates policy IDs,
actor/scope, duplicates, bounded file sizes and original cost limits. Public peer
clients enforce their existing local endpoint/route/authentication bounds. Only
Planning SQL is opened, with serving-role verification and5s statement timeout.

Provider defaults to disabled; run may still assemble/publish context and recover
prior issuance. Explicit openai_curation_v1 requires the existing synthetic-only,
exact-scope LiveCurationSettings. No fixture provider is available in production
configuration. Check never loads its key; run loads it only after DB readiness.
Policies cannot widen the original4call/$1 scope guard or$.25 reservation ceiling.

CurationPeers composes original public readers, derived publication and existing
compiler clients. CurationHost owns DB lifetime, fixed internal grants and polling;
no startup grants another owner permission. Existing retained declaration/input/
issuance/selection wins over current settings. A processing denial after freeze
pauses without a model call; recovery never substitutes newly read context.

Verification:15 configuration/process checks;2 actual process-death/recovery and
processing-denial checks;15 policy-rejection/boundary checks. Issuance crash uses a
test-only provider, exits73 before observation, expires job coordination, then runs
the actual configured CLI with provider disabled. Original dispatch becomes unknown,
retains full reservation, and repeated replacement stays idle with one dispatch.
CLI errors are redacted; unexpected integrity failures remain fatal and inspectable
through retained history. No paid calls or real credentials in this qualification.

Last reviewed:2026-10-12 00:50:48 America/Chicago. Architecture: [Planning](../../../../../docs/Architecture/Agents/Planning.md).
Delivery: [UI-01.08](../../../../../docs/Build%20Plans/UI-01.08%20Campaign%20curation%20boundary%20decision.md).
Independent replacement: curation-installation-20261012a,205 scoped checks, public-only wheel closure.

UI-01.08/P3.2c: CurationHost also composes capability_fulfillment via public Registry
metadata and Data processing readers. It retains the same fixed execute_curations
principal, without fulfill_capabilities submission authority. Readiness requires0027.
Polling alternates fulfillment/campaign turns with idle fallback; one pending tool
review cannot starve campaigns. Provider-disabled processes can verify already
owner-authorized fulfillment commands. No startup scientific/tool grants or model
calls are introduced. See capability_fulfillment README for failure/replay semantics.

Planning0.127 independently installed qualification passed150 capability/intake/worker
checks458.67s, including compiler and process crash recovery. Evidence:
capability-installation-20261012a/evidence.json. No paid calls/demo upgrade.


P4.4a integration repair, Planning0.127.1: CurationPeers supplies RegistryReader
and RuntimeMetadataReader to compiler refresh. Capability acceptance receives its
own composed AcceptanceCollector over the Registry metadata transport and Data
reader. These interfaces differ: refresh validates exact release/universe records;
acceptance reads a public release DTO before verifying fulfillment evidence. They
must not be interchanged. The production-composition regression calls all three
interfaces with literal public records. No schema, original proposal, command or
receipt changes; an already-retained compiler selection resumes without provider
reissue after process replacement. Actual owner qualification remains P4.4.

Planning0.138/UI-01.08j adds private planning-curation-worker.v2 configuration.
actor_id still owns the human curation/policy/claim/publication. Explicit
runtime_actor_id selects the separately authorized Runtime author; eligibility.actor_id
selects the Registry reader. Existing CompilerSelection already persists all three
identities independently; CompilerStore checks their original bindings on replay.
This exposes existing behavior, with no new public API, migration, impersonation
mechanism or grant. V1 still rejects alternate peer identities and has unchanged
defaults; V2 requires an explicit Runtime actor. Peer services retain unique
identity configuration and enforce their own restricted actions. No admission grant.
