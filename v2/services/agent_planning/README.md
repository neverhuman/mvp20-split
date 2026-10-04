# Agent Planning service boundary

- Version: Planning0.30.0; public Planning0.7.0. BP-07.02 complete and audited;930 installed tests,39 process/replay stages and actual-owner recovery verified.
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
