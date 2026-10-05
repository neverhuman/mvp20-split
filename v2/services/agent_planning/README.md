# Agent Planning service boundary

- Version: Planning0.46.0; public Planning0.8.0. BP-07.02 complete and audited;930 installed tests,39 process/replay stages and actual-owner recovery verified.
- Owner: Agent Planning. Runtime accepts execution decisions; Knowledge and Research retain domain authority.
- Design: [Planning](../../docs/Architecture/Agents/Planning.md). Canonical progress: [BP-07.02](../../docs/Build%20Plans/BP-07/Completed/BP-07.02%20Reliable%20text%20decomposition.md).

## Responsibilities and exclusions

Planning binds immutable context, deterministic provider attempts, conservative budgets and attributed text-decomposition proposals. It persists its own intent and exact outputs before publishing derived Artifacts or handing proposals to their accepting owners. It has no public server or live model adapter and cannot execute a campaign, register scientific truth, grant source rights or mutate a peer's tables.

This service is an independent wheel. Public contracts and the Tool Protocol SDK are peer dependencies; SQLAlchemy/psycopg/Alembic are private persistence dependencies. Private peer imports, shared ORM models and peer SQL are forbidden. Scientific uncertainty, contradiction and missing evidence remain explicit; they do not impose a global campaign veto.

## Owned modules

| Module | Boundary |
|---|---|
| [context](src/amphora_agent_planning/context/README.md), [providers](src/amphora_agent_planning/providers/README.md) | Immutable scoped requests, explicit omissions, physical attempts, bounded capture and closed output-profile catalog |
| [budget](src/amphora_agent_planning/budget/README.md), [persistence](src/amphora_agent_planning/persistence/README.md), [orchestration](src/amphora_agent_planning/orchestration/README.md) | Conservative reservations/settlements, owned journals and once-only local dispatch; truthful deadline uncertainty and late evidence |
| [extraction](src/amphora_agent_planning/extraction/README.md) | Versioned task/source/prompt binding, UTF-8 quotation geometry and interpretation-only failed/repaired traces |
| [source_access](src/amphora_agent_planning/source_access/README.md), [peer_reads](src/amphora_agent_planning/peer_reads/README.md) | Bounded authenticated public reads, current Data processing permission and complete consumed-input ancestry |
| [publication](src/amphora_agent_planning/publication/README.md) | Immutable trace publication intent, fenced journal and bounded Data upload/receipt recovery |
| [proposals](src/amphora_agent_planning/proposals/README.md), [knowledge_access](src/amphora_agent_planning/knowledge_access/README.md) | Exact pinned Knowledge records and candidate entity/assertion/edit validation; Knowledge alone accepts changes |
| [research_proposals](src/amphora_agent_planning/research_proposals/README.md), [research_access](src/amphora_agent_planning/research_access/README.md) | Distinct question, candidate-answer and evidence-need proposals bound to exact selected Research revisions |
| [repair](src/amphora_agent_planning/repair/README.md) | Immutable root/member authority, aggregate attempt/exposure ceilings, retained diagnostics and bounded child execution |
| [result_publication](src/amphora_agent_planning/result_publication/README.md) | Exact diagnostic/candidate-answer Artifacts, current-rights preparation and separate durable publication slots |
| [owner_handoff](src/amphora_agent_planning/owner_handoff/README.md) | Immutable owner requests/dependencies, read-first reconciliation and bounded question/need/answer/graph coordination |

## State, effects and recovery

Planning owns planning_0001 through0011. Histories and prepared bytes are immutable; separate controls carry database-clock leases/fences. Normal imports never apply migrations. No SQL lock spans provider or peer I/O. Publication commits intent before PUT; uncertain streams use bounded successor uploads and uncertain finalization recovers the original receipt. Handoff reads the original owner identity before any new POST, checks fresh processing rights for new effects and requires exact accepted readback. Terminal replay does not read peers. A process exit does not release its lease; recovery waits for real expiry.

Local Research dependencies require the exact acknowledged question. Independent effects continue when another lane is unavailable. Knowledge conflicts never rebase a task automatically. Accepted typed corrections inform explicitly selected future tasks; original campaign/task pins and history remain unchanged. Quote geometry and structural acceptance are not semantic entailment or scientific sufficiency.

## Replacement and verification

Tests belong under this owner's tests/ behavioral folders; dev/test_scopes.json registers granular runs. Example: dev/run_tests.py --module agent-planning --area proposals. dev/verify_planning.py builds two independent wheel installations, excludes private peer implementations and checks owned SQL history across replacement. Actual-owner, semantic-corpus and abrupt-exit harnesses are separately documented in [acceptance](tests/acceptance/README.md). [Evidence](../../docs/Audits/Evidence/BP-07-Extraction/) records scoped line/branch gaps, process identities and synthetic limits; the tracker owns current percentages.

Replacement must preserve canonical bytes/hashes, actors/scopes, source identities, omissions, budgets, attempts, pinned revisions, historical output profiles and immutable migration history. Never run Planning<=0.28 migrators on0011. Replace old admission writers before enabling repair families: Planning<=0.20 does not enforce aggregate family ceilings, and Planning<=0.22 lacks prepared repair workflow handling. Read the persistence/repair contracts before cutover; retained state is not disposable test setup.

Real provider/model, egress and spend remain owner choices before actual calls. Full context-body assembly, actual tokenizer/window fit, campaign proposal compilation, Runtime engagement acceptance and live scientific evaluation remain successor gates. The reviewed synthetic corpus measures explicit software-oracle accounting, not human expert agreement, real-model accuracy or scientific validity.


[campaign_context](src/amphora_agent_planning/campaign_context/README.md) adds pure exact Research selection/request binding and selected-record/relevance projections under BP-07.03/B1.01. Context assembly and campaign proposal compilation remain later gates; the closed extraction boundary is unchanged.

[campaign_research_access](src/amphora_agent_planning/campaign_research_access/README.md) supplies bounded exact Research record reads and per-record safe failure reports. Actual Research compatibility is verified under the scoped BP-07.03/B1.02a.iii gate.

[research_view_access](src/amphora_agent_planning/research_view_access/README.md) binds explicitly selected specimen/property/series pages and reviewed catalog schemas to the original campaign request. No hidden pagination or scientific acceptance.

[registry_access](src/amphora_agent_planning/registry_access/README.md) owns bounded current inventory/exact full-lock observations through [metadata_reads](src/amphora_agent_planning/metadata_reads/README.md), a separate closed Registry/Runtime GET boundary. Discovery preserves lifecycle and partial results; it does not confer eligibility or compiler review.

[runtime_metadata](src/amphora_agent_planning/runtime_metadata/README.md) verifies the reviewed compiler universe and selected exact schema bytes, preserving partial failures and original pins. Actual compilation/admission stays Runtime-owned.

[campaign_data_access](src/amphora_agent_planning/campaign_data_access/README.md) selects exact campaign Artifact references and captures fresh processing-authorized bytes, preserving per-reference failures without retaining an access lease.

[retrieval_access](src/amphora_agent_planning/retrieval_access/README.md) verifies exact retained Data query/result and source-binding identities; retrieval history does not grant fresh processing access or scientific confidence.

[campaign_knowledge_access](src/amphora_agent_planning/campaign_knowledge_access/README.md) reads exact pinned campaign graph context through public Knowledge endpoints. [graph_context](src/amphora_agent_planning/graph_context/README.md) owns shared pure record invariants; extraction retains its original adapter and byte identities.

Actual combined-owner context verified 2026-10-04 18:55:41:10 isolated Planning workers,9 Registry/Runtime/Data/Knowledge hosts, retained PostgreSQL/Qdrant and original/future graph selections. Exact reads, partial/denied/foreign outcomes, restarts and fresh processing permission changes passed; Research unchanged-client proof reused explicitly. See docs/Audits/Evidence/BP-07-Campaigns/Combined_Owner_Context.json. Context assembly/token fitting and live provider quality remain later gates.

[campaign_graph_context](src/amphora_agent_planning/campaign_graph_context/README.md) projects exact selected graph records and endpoint/alias/retraction dependencies, with bounded bytes and relevant positive/absent observations. Whole-graph origin is preserved without making unrelated changes a blanket invalidation.

[campaign_artifact_context](src/amphora_agent_planning/campaign_artifact_context/README.md) plans all four required roots plus128 entries, merges roles and performs mandatory-first bounded processing reads under one shared budget. Raw bodies remain data, with explicit unavailable items and no continuing rights grant.

[campaign_research_context](src/amphora_agent_planning/campaign_research_context/README.md) recomputes selected Research findings and projects exact named pages, explicit gaps and relevant observations without pagination, quality filtering or a source-processing grant.

[campaign_tool_context](src/amphora_agent_planning/campaign_tool_context/README.md) preserves distinct Registry observations and complete selected Runtime schema outcomes. [campaign_retrieval_context](src/amphora_agent_planning/campaign_retrieval_context/README.md) retains original query/result provenance or explicit unavailability. Both remain data for later budgeted assembly, not tool or scientific authority.

[campaign_packet_profiles](src/amphora_agent_planning/campaign_packet_profiles/README.md) owns reviewed campaign instructions, exact fixture tokenizer identity and measured packet ceilings preserving the original output reserve. Synthetic byte counts do not establish live-model fit or authorize dispatch.

[Campaign slice plan](src/amphora_agent_planning/campaign_slice_plan/README.md) composes revalidated owner inputs as required-before-optional byte-owned data, preserving original omissions and per-slice observations. Individual inventory releases can be budgeted independently; full packet fitting and journal remain subsequent.

[Campaign packet](src/amphora_agent_planning/campaign_packet/README.md) renders reviewed instructions separately from observed data and measures the entire required/optional envelope, omissions and consumed observations under the original fixture budget. No provider or journal authority.
