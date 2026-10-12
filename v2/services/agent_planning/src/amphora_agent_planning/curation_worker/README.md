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

Current implementation: discovery/heartbeat/lifecycle/polling; configured process and installed replacement proof remain. Tests owned by
 tests/curation_worker and curation_jobs. No model key, network call or startup
occurs through these primitives alone. Existing heartbeat strict-revision API
remains unchanged; refresh is the managed keeper's original-fence operation.

CurationWorker.tick claims one job, keeps its fence alive and advances one phase:
original declaration/public context and input freeze; original provider issuance/
result; or one existing compiler step. Recovery of retained input/declaration is
before current policy lookup. Original receipt/proposal remains immutable. Missing
provider stays pending; bounded budget/preparation/publication failures retain named
status. Typed transport uncertainty stays pending for original receipt recovery;
unexpected integrity/programming errors propagate. CLI/configuration remains pending.

CurationPoller advances one selected job per turn, wraps its keyset cursor fairly,
checks a stop event between bounded turns and enforces finite polling deadlines.
No provider retry is authorized by another turn. Original-context timeouts pause;
active predecessor/denied sources fail before provider.36 worker/job tests pass.
