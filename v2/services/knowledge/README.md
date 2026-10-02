# Knowledge Service

- Package: amphora-knowledge0.5.0; BP-06.02/B1 complete; B2 rebuild publication active.
- Design: [Knowledge](../../docs/Architecture/Knowledge/Knowledge_Architecture.md), [activation](../../docs/Audits/BP-06.02_Activation.md).

Knowledge owns domain entity/assertion identity, typed structural edits and deterministic accepted-history reconstruction. The package implements pure [authoring](src/amphora_knowledge/authoring/README.md) and [replay](src/amphora_knowledge/replay/README.md). The [private persistence module](src/amphora_knowledge/persistence/README.md) now commits proposals/decisions/logs/snapshots/heads and preserves stored profiles. [Reference validation](src/amphora_knowledge/validation/README.md) now implements bounded public clients and provenance checks; actual-peer integration and [authenticated HTTP](src/amphora_knowledge/transport/README.md) are verified; rebuild publication remains pending. Domain evaluation and a valid accepted-change DTO are not durable acceptance.

Dependencies are public Core0.1.0, Knowledge0.3.0, evidence0.5.0 and Research0.2.0 contracts plus FastAPI/Uvicorn, SQLAlchemy/psycopg/Alembic and the standard library. There are no private Data/Research imports, cross-owner SQL, shared ORM, source payload storage, LLM calls or campaign execution. The validation workflow checks scope/action before I/O and reads public Data/Research routes; actual-owner integration and HTTP credential binding are verified.

Structural acceptance preserves reported/hypothesized/unresolved assertions; it grants no scientific truth, constraint eligibility or permission to consume source payloads. Questions and evidence needs remain Research declarations. Typed operations retain corrections, aliases, contradictory contexts and retractions; replay never reinterprets descriptive prose. Graph publication must not change a campaign's pinned knowledge revision.

Tests are module-owned under tests/authoring, tests/replay, tests/persistence, tests/validation, tests/api and tests/acceptance; use dev/run_tests.py --module knowledge, optionally --area authoring or --area replay. B2 rebuild publication, B3 actual concurrency/crash cases and V1 independent service/peer replacement remain required gates. Replacements must preserve canonical hashes, exact prior references, nonpromotion, safe failure codes and independently specified history semantics, not merely DTO validity.

Earlier pure-module checkpoint:36 owner tests and36 independent installed-owner tests pass;26 authoring and10 replay cases. Combined measured coverage319/334 statements and124/140 branches; remaining defensive error branches are listed in the committed Domain_Replay evidence. No transaction or scientific-authority coverage is inferred from this pure suite.

Persistence checkpoint:47 owner tests (11 real PostgreSQL) and33 Knowledge contract tests pass together in an independent installation with no Data/Research implementation;0 skipped.258 schemas preserve all256 predecessors. Private ledger observations remain synthetic fixtures until the public-peer validator is implemented; the B1 delivery is still open.

Validation checkpoint:83 owner tests pass (13 actual PostgreSQL);36 validation cases include scripted-record rules, real loopback scripted HTTP and durable workflow failure/retry. Scripted peers do not establish actual-owner compatibility. Public schemas and knowledge_0001 remain unchanged.

Latest B1 proof:104 owner tests pass (26 PostgreSQL), including an actual three-process Data/Research/Knowledge test and Knowledge restart.35 contract and14 dev checks pass. Full in-process coverage980/1075 statements and289/348 branches; subprocess scenarios are separately recorded in Public_API evidence.260 schemas preserve258 predecessors. Independent wheel replacement and mid-build process death are not inferred from this checkpoint.

B2 cursor checkpoint:112 owner tests pass, including18 replay cases. Exact watermark catch-up preserves canonical bytes and prior verified state on failure. Durable rebuild materialization publication remains pending; child completion stays25%.
