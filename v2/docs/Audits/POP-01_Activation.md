# POP-01 activation and compatibility inventory

- Reviewed: 2026-10-13 18:26:00 America/Chicago.
- Baseline: `a614e594`; UI-01/V1 and UI-02/P4 closed and archived.
- Disposition: `corrected_ready` for E1 design; new public contracts await owner
  decision. No population implementation, performance or deployment credit.
- Owner: [POP-01](../Build%20Plans/POP-01%20Population%20Campaign%20Execution%20and%20Experience.md).
- Next: [E1 boundary decision](../Build%20Plans/POP-01.04%20Population%20contract%20decision.md).

## Coherence review

The objective remains a stable scientific method graph with separate population,
generation and occurrence views. Execution precedes Experience, which precedes
Qualification. Twelve equal child gates remain the progress basis; all are 0%.
The existing Knowledge/LLM workflow and supplied-structure inspector meet the entry
dependencies. Neither establishes molecular evolution or scientific model accuracy.
Deterministic engineering fixtures need no new dataset or paid calls at E1.

Ownership is unchanged: Search proposes populations and selection; Runtime alone
accepts execution, dispatch and transitions; Data protects immutable artifacts;
Research owns scientific identities/evidence; Planning proposes reviewed composition;
Studio projects accepted history. No population scheduler service is introduced.
Each child retains scoped tests, actual-owner evidence and an audit exit. Recovery,
1000-member qualification and the 19-stage process fixture remain mandatory.

Corrections at activation:

1. UI-02 is now complete; replace queued/pending prerequisite language with the E1
   decision gate. Planning maturity does not increment implementation percentages.
2. Existing scatter already freezes membership and atomically advances its cursor
   with child creation. Do not design a second dispatch authority from scratch.
3. Collection/scatter cardinality already permits 1000 members, but this does not
   establish payload, retained-page, total activation or global invocation capacity.
4. UI-02 discovery scans at most two pages/100 nodes. Reuse its protected exact-candidate
   detail, not its bounded discovery as a population index. U1 still owns that index.
5. Root Runtime README contains historical current-state statements. Read current
   package/source and focused module contracts; existing DOC-004 owns cleanup.

## Source inventory and compatibility boundary

Paths are relative to `v2/`. Observations below are source facts, not scale proof.

| Boundary | Current source / behavior | POP disposition |
|---|---|---|
| Search specification | `contracts/search/src/amphora_contracts_search/specification.py`: population 1..128, one evaluator, 16 objectives, 32 dimensions | Preserve exact v1; add distinct population/method profile |
| Search checkpoint | Same package `checkpoint.py`: 256 attempts/ranks/observations, 128 survivors; predecessor reference | New reference-backed immutable pages; no widening old arrays |
| Graph-step transport | `contracts/search_steps/src/amphora_contracts_search_steps/models.py`: 128 requests/results and inline checkpoint | Add separately identified step schemas; preserve old roots |
| Ranking | `tools/evolution_search/src/amphora_evolution_search/ranking.py`: hard 256-member guard; deterministic constrained Pareto/crowding | Reuse mathematical behavior behind explicit new bounded entry; keep original guard/goldens |
| Missing fitness | Search `reduction.py`, `evaluations.py` and module README: unavailable fitness stops old search | New frozen exclusion/minimum-parent policy; never substitute zero |
| Payload | Search adapter/README: 262144-byte input/output | Page references and measured total bounds; no global cap relaxation |
| Graph values | `contracts/graph_runtime/src/amphora_contracts_graph_runtime/values.py`: collections up to10000 | Existing cardinality sufficient; nested collections are not present values |
| Graph controls | Campaign `executable/nodes.py`: scatter max_members10000/max_parallel1024; multi-input Invoke and explicit joins/loops | Reuse named scientific subgraphs, no candidate copies in authored topology |
| Artifact conversion | Campaign `executable/bindings.py`: 262144-byte conversion, max_artifacts1024, max_items10000 | Reference/page composition must respect cumulative conversion budget |
| Dispatch | Runtime `coordinator/expansion.py`: frozen membership, next_index, active child count, child insertion and cursor update in owner transaction | Reuse identity/lease/fence machinery; max_parallel limits child scopes, not all nested tool invocations |
| Run budget | Graph-runtime `models.py`: max_activations100000, deadline up to86400s | Product of generation/process/population limits must fit the admitted run; maxima are not independently attainable |
| Material lineage | Numeric `candidates.py`: at most two genetic parents | Separate material derivation records; never reinterpret genetic ancestry as reaction inputs |
| Candidate view | Studio candidate_inspector module contracts | Reuse exact protected representation/provenance; population aggregation is new U1 scope |

The remaining E1 implementation must provide producer/consumer maps, schema goldens,
intrinsic validation, transition/write sets and an executable composition proof.
Nested page scatter can reuse existing controls, but page concurrency alone does
not prove a campaign-wide tool invocation ceiling. Do not mark E2 ready until the
global resource policy and aggregate byte/activation budgets are tested.

## Verification

2026-10-13 18:22:39 America/Chicago: existing Search wire and numerical ranking suites
passed **37 tests** in 4.11s:

`v2/dev/.venv/Scripts/python.exe -X utf8 -m pytest v2/contracts/search/tests/checkpoint v2/tools/evolution_search/tests/ranking -q --tb=short`

This is a compatibility baseline only. No new DTO, migration, execution profile,
scientific tool, paid model request or population runtime was implemented.
