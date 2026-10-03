# Knowledge Accepted History Persistence

- Status: BP-06.02/B1 complete; private PostgreSQL boundary, authenticated HTTP and actual-peer review implemented.
- Migration: knowledge_0001 is applied to the retained fixture; knowledge_0002 adds rebuild projections; knowledge_0003 adds sibling reasoning histories; all applied migrations are immutable; knowledge_0004 adds publication selections and worker leases.
- Design: [authoring](../../../../../docs/Architecture/Knowledge/Authoring.md), [activation protocol](../../../../../docs/Audits/BP-06.02_Activation.md).

KnowledgeLedger owns immutable graph profiles, proposal intents, terminal decisions, accepted operations, full snapshots and a mutable current head. It uses only knowledge schema tables. Principal comes from a trusted owning adapter; propose_graph/read_graph grants and exact scope are checked before SQL. Sibling transport and validation modules authenticate bearer tokens and validate actual public Data/Research responses.

begin registers exact canonical proposal bytes, their hash and actor under scope/graph/change ID. The first intent also persists the configured vocabulary and structural-policy definition. Profiles never change with new process defaults; stored definitions are validated and reconstructed for existing graph replay. An exact same-actor retry returns its original status; changed bytes or actor conflict. GraphProposalStatus distinguishes unknown (no record), pending (decision=null) and an immutable terminal decision. Pending is not acceptance.

accept replays the owner's ordered accepted log outside the write transaction using the stored profile, checks the supplied exact reference observation and computes a candidate snapshot. The observation is adapter-supplied input, not proof that the adapter contacted a peer. A short graph-scoped advisory lock then reconciles any prior decision, checks the complete expected head and commits accepted operation, snapshot, new head and decision together. A moved head produces an immutable conflict; semantic failure produces a retained rejection without entering replay. Duplicate concurrent delivery returns the first committed receipt. No SQL lock spans public HTTP or model/file access.

The accepted-log/snapshot tables have a mutually constrained exact binding, with the accepted-to-snapshot foreign key deferred to transaction commit. A half-pair cannot commit. Head foreign keys bind the same position/change/hash/snapshot. Predecessor checks explicitly reject NULL for positions after1. Service grants allow SELECT/INSERT histories and only head-field UPDATE; UPDATE/DELETE of profiles, proposals, decisions, accepted records and snapshots are denied. Possession of database service credentials remains trusted infrastructure authority; per-request scope is enforced by the owning adapter/ledger.

Limits are explicit:256KiB canonical proposal,1MiB accepted record,16MiB snapshot,10000 accepted changes and64MiB cumulative accepted-log bytes per graph. Admission prevents committing a history that exceeds the subsequent bounded replay reader. Rejections remain attributable; storage/infrastructure faults propagate instead of fabricating acceptance. An acceptance failure rolls back log/snapshot/head/decision while retaining the separately committed intent. Retry reconciles the same identity.

Exact historical snapshot/change reads validate graph/revision/change/digest; profile reads return the stored universe or observational new-graph default without writes; they do not return an implicit latest revision. Replacing the ledger with different new-graph defaults preserves old graph profiles, history and receipts. A schema/policy migration is not accomplished by changing defaults or reinterpreting old log records. The current profile is immutable per graph; explicit migration support requires its own versioned mapping.

Records.py owns canonical proposal projection, receipt construction and stored profile restoration. Ledger.py owns SQL/transaction composition. Pure edit and replay behavior remain in their sibling modules. migrate.upgrade explicitly uses knowledge_migrator; no automatic migration at service startup. Packaged SQL accompanies the wheel.

Verification: tests/persistence owns11 PostgreSQL cases covering pending/accepted replay, stored profiles, actor/content conflict, concurrent writers, rollback and SQL constraints/grants. Additional rebuild, API and process suites are separately owned. Whole-owner coverage/gaps and exact process identities are maintained in plan evidence, not inferred from SQL tests.

Snapshot reads prefer a published materialization only for the exact requested semantic reference, then fall back to the original immutable snapshot. Both paths verify identity and content hash. knowledge_0002 owns rebuild audit and pointer tables in the sibling rebuild module; knowledge_0001 is unchanged.

knowledge_0003 tables are owned by the [reasoning store](../reasoning/README.md), with exact snapshot/profile foreign keys and immutable intent/decision records. The accepted graph ledger and its first two migrations remain unchanged.

knowledge_0004 tables belong to the [publication store](../publication/README.md). Immutable selections reference terminal reasoning decisions; separately mutable DB-clock leases support short fenced transactions. No payload/attempt orchestration exists yet.0001..0004 are applied and immutable.

knowledge_0005 adds immutable publication payloads and append-only attempt events (SELECT/INSERT only), owned by the publication journal. Applied migrations0001..0005 are immutable.

knowledge_0006 owns immutable publication terminals, pairing derived artifact metadata and synthetic logical receipt at one journal position. Failed finalization retains a matching original-command rejection proof; uncertainty cannot become failure without it.0001..0006 are applied/immutable.

knowledge_0007 adds append-only receipt correction records, owned by the [correction module](../corrections/README.md). The latest committed ordinal is the chain head; expected-head checks and scoped advisory locks serialize mutation. Service role SELECT/INSERT grants preserve all older records/publications. Source selection restores the original graph/publication/actor under a distinct correction grant. No existing migration is changed.
