# Agent Planning service boundary

Version0.1.0, BP-07.01/B1.01. This isolated owner currently implements only pure context/request validation and physical-attempt binding. It has no server, database, provider dispatch, live credentials, output publication or Runtime acceptance implementation yet. [Design](../../docs/Architecture/Agents/Planning.md) describes the larger target; [build plan](../../docs/Build%20Plans/BP-07/BP-07.01%20Model%20and%20engagement%20contracts.md) owns current progress.

Public dependencies are planning/core contracts. Private modules group behavior with its data; transport DTOs do not own policy. Context owns scoped immutable input snapshots. Subsequent providers and persistence modules will own bounded call parsing and private request/attempt history respectively. Runtime alone accepts execution decisions; Knowledge and Research retain domain authority. No peer private imports, shared ORM or peer-table reads.

Tests live under tests/context; dev/run_tests.py --module agent-planning --area context --coverage selects them. Replacement must preserve canonical bytes/digests, explicit omission semantics, caller isolation, budget/input bounds and attempt identity. Current fixture records are synthetic and not owner existence, current-rights, tokenizer or model-quality proof. Real model/provider, egress and spend policy require owner selection before calls.
