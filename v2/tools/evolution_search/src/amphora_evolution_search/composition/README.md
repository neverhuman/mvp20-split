# Authored population composition preflight

Owner: POP-01.01/E2.3. This module is under implementation; complete composition
and batch/cap qualification are not claimed. Search owns this pure authoring
assessment. Runtime alone compiles/adopts plans, admits work and enforces capacity.

The first component bounds the expanded wire-v4 graph: every authored activation,
scope, named tool call, materialization and declared binding budget. Scatter total
work uses max_members; concurrent queued work uses active child scopes. Sequential
iterations multiply work but do not multiply concurrent width. Active-attempt caps
do not reduce the queue bound. Every reachable or potentially unreachable authored
invoke is accounted for; speculative branch pruning is not used. Empty scatters
retain authored binding identity while expanding no child work. Retry budgets
include every counted invocation, not just evaluation methods.

Counts use checked safe integers and a bounded supported scope depth. Await nodes
are outside this first finite numerical composition profile. Positive counts are
not graph admissibility, execution authority, physical throughput or full resource
preflight. A supplied compiled document/definition is hash-checked against an
expected plan hash; the caller must obtain that expectation from its trusted owner
flow. This does not prove admission by itself. Spec/release pins, worker publication/ancestry/envelope and
validation I/O accounting remain to be integrated. Runtime's compiler/owner gates
remain authoritative. No service implementation, network, filesystem or private
state access belongs in this module. Source-owned tests live under tests/composition.

Fifteen focused checks cover nested expansion, serial loop width, batch-dependent
orchestration, queue saturation, retries, empty scatters, binding budgets, branch
conservatism, overflow/depth and compiled-plan identity. Full source401 passes;
independent verification is recorded in the POP-01_Composition_Preflight audit.

PublicationLedger now assesses an explicit prospective publication DAG. Publication
records include every admitted input carrier and declared parent. External source
closure must be established by the caller; absent parents fail instead of being
assumed leaves. Insertions are topological, so forward edges/cycles reject. Direct
parents stay within128; the result plus its distinct ancestors stay within4096.
Shared ancestors count once, and conflicting identities reject. Failed additions
do not mutate the ledger. Retained root unions report unique content bytes only;
receipt, database and provider overhead are not estimated. Grouping does not shrink
closure. This primitive has no owner I/O and does not establish source evidence or
produce worker cost profiles; those integrations remain the next E2.3 delivery.

PageEnvelope bounds byte-aware packing from caller-established maximum canonical
row and empty-page header bytes (including the largest ordinal). It charges commas,
uses both64 rows and131072 bytes per page, rejects oversized rows/single-row pages,
and produces a PageFootprint. Combining footprints enforces the aggregate512-page/
64MiB closure across families and retained history. Empty row sets create no pages.
These supplied maxima still require per-profile evidence; this primitive does not
prove an arbitrary future DTO fits its row envelope. Ten focused tests exercise
byte-first splitting, row-first splitting, exact byte fit, empties, combined closure
and invalid/overflow counts.

PageEnvelope.population derives full header maxima for seven reviewed public
population page DTOs. The bounded JSON-schema subset includes closed objects,
finite arrays, bounded strings/integers, literals and local acyclic references;
unbounded numbers/maps/strings and unsupported shapes reject. It charges all
optional/default fields and worst JSON string escaping. No prospective ArtifactRef
is fabricated. Row maxima still require the reviewed operation's enforcement or
a stronger per-row proof. The size assessor does not validate payloads or establish
owner admission. Tests include large valid public metadata and escaping.

NumericPublicationProfile maps every named numeric population operation to a
source-reviewed publication upper count using the frozen population/method maxima
and schema-derived headers with enforced8192-byte row caps. Counts include all
birth dispositions, contexts, method outputs/evidence, manifests, proofs, checkpoints,
request adapters, successor preparation and120-reference grouping intermediaries.
Unknown capabilities and mismatched release/image/contract pins reject, including
zero-expanded bindings. The graph's materializations are counted once; every worker
call receives its full retry allowance. Content storage upper bytes use worker
262144-byte caps plus graph-declared binding bytes (including conservative read
budgets), not an assumed cap for graph materialization. CPU, provider/storage
overhead, validation I/O, complete ancestry and actual future row suitability remain
outside this component. Per-call publication counts above4096 reject. This component
may conservatively reject large configurations pending tighter row profiles.
The1000-birth production publication fixture stays below its assessed seed bound.
