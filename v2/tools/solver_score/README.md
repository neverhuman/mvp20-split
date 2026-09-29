# Synthetic solver score

Accepted checkpoint `2026-09-29 17:57:39`: BP-04.04 closed/audited. Five real solver images and independent tool/SDK/owner installs passed initial-population -> successor generations 1/2, concurrent scoring and Runtime replacement; 17 invocations, all 44 reservations confirmed. Source/lineage/receipt/artifact history preserved. Scientific validity and target-host execution remain excluded. Earlier B1-B3 statements below describe their historical verification tiers; no gate in this child remains open.

- Owner: BP-04.04; B1 stage/standalone installation verified, release 0.1.0. Actual graph process/peer gates passed B3/V1.
- Boundary: Evaluate one synthetic candidate through the source-pinned ordered module envelope fixture.
- Input/output: public `amphora-contracts-solver-fixture` ScoreRequest -> ScoreResult; exact bytes in `src/amphora_solver_score/schemas`.

Evaluate one candidate into envelopes in the exact packaged source molecule-chain order. These are deterministic synthetic envelopes, not calls to the v1 scientific modules. A configured module error produces `ERROR`/`NO_AUTHORITY` and preserves all later envelopes. A configured whole-candidate scoring failure instead rejects the invocation and publishes no successful score. Unknown module names/source pins reject. Every successful result preserves its complete candidate identity/seed record, `ranked=false`, zero eligible objectives and zero display score. No numerical fitness or molecular-validity inference is permitted.

This independently packaged pure tool owns its stage algorithm, packaged frozen-source pins, schema bytes, descriptor and module-local tests. The public fixture contract package contains wire records only. No sibling tool or service private imports, database, campaign scheduling, graph iteration or scientific acceptance belongs here. Molecular structure is unchanged, ranking authority is absent and capability envelopes remain synthetic/NO_AUTHORITY.

`python -m amphora_solver_score compute` reads bounded JSON and writes JSON. `describe --image-sha256 <actual image SHA>` binds its descriptor to an externally built image; test digests are never deployment evidence. `worker --config <path>` uses the public SDK to execute one Runtime-issued Artifact invocation. Runtime owns attempts, leases, retries and acceptance; Artifact owns immutable bytes and retention. Invalid source/data stops with a safe fixture rejection, never echoes input or silently invents a population.

`boundary.py` owns packaged source-pin verification. `kernel.py` owns focused stage domain behavior and explicit DTO conversion. `adapter.py` maps failures to the public worker protocol. `metadata.py` owns schema/descriptor publication. Replacement must preserve deterministic identity, seed/order semantics, exact schemas, source pins and failure vocabulary, or publish a new immutable release. No network effects beyond configured worker infrastructure are allowed.

Tests live in `tests/kernel/`; cross-stage and graph oracles belong to Runtime `tests/baseline` and its source-pinned fixtures. Independent wheel/schema/CLI installation passed B1; actual images, new-tool peers and replacement passed B3/V1. DGX/ARM performance, biological validity and actual evolutionary structure mutation remain outside this fixture.

B1 focused coverage (`2026-09-29 16:59:32`): 48/90 package statements and 6/16 branches; kernel 17/18 statements and 3/4 branches. These are parent-interpreter measurements across 42 pure fixture cases; CLI goldens run in separate processes and are not counted as covered lines. Remaining gaps include adapter/CLI paths and defensive invalid-state branches; B3 owns the expanded failure matrix. No blanket coverage claim.
