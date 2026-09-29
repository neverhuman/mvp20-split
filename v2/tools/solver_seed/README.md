# Synthetic solver seed

- Owner: BP-04.04; B1 stage/standalone installation verified, release 0.1.0. Actual graph process/peer gates remain B3/V1.
- Boundary: Produce the bounded initial synthetic population; preserve rejection-compacted scoring seeds.
- Input/output: public `amphora-contracts-solver-fixture` SolverConfig -> ProposalBatch; exact bytes in `src/amphora_solver_seed/schemas`.

The initial batch is generation zero. `c0` is the original candidate, never a mutation-rejection target; `c1` through `cN` are readable fixture mutation IDs with parent `c0`. Proposal seeds are `seed + original_index`; scoring seeds are `seed + accepted_index`, compacted only after rejections. The batch carries an empty predecessor state at generation -1, ordered score requests and explicit rejection records. Fault-module names must exist in the packaged molecule-chain reference; changed source pins reject before proposal work. Population is 1..8 and offspring generations 0..8. Structure is a fixed unchanged marker; IDs are not native molecular hashes.

This independently packaged pure tool owns its stage algorithm, packaged frozen-source pins, schema bytes, descriptor and module-local tests. The public fixture contract package contains wire records only. No sibling tool or service private imports, database, campaign scheduling, graph iteration or scientific acceptance belongs here. Molecular structure is unchanged, ranking authority is absent and capability envelopes remain synthetic/NO_AUTHORITY.

`python -m amphora_solver_seed compute` reads bounded JSON and writes JSON. `describe --image-sha256 <actual image SHA>` binds its descriptor to an externally built image; test digests are never deployment evidence. `worker --config <path>` uses the public SDK to execute one Runtime-issued Artifact invocation. Runtime owns attempts, leases, retries and acceptance; Artifact owns immutable bytes and retention. Invalid source/data stops with a safe fixture rejection, never echoes input or silently invents a population.

`boundary.py` owns packaged source-pin verification. `kernel.py` owns focused stage domain behavior and explicit DTO conversion. `adapter.py` maps failures to the public worker protocol. `metadata.py` owns schema/descriptor publication. Replacement must preserve deterministic identity, seed/order semantics, exact schemas, source pins and failure vocabulary, or publish a new immutable release. No network effects beyond configured worker infrastructure are allowed.

Tests live in `tests/kernel/`; cross-stage and graph oracles belong to Runtime `tests/baseline` and its source-pinned fixtures. Independent wheel/schema/CLI installation passed B1; actual images, new-tool peers and replacement remain B3/V1 gates. DGX/ARM performance, biological validity and actual evolutionary structure mutation remain outside this fixture.

B1 focused coverage (`2026-09-29 16:59:32`): 54/96 package statements and 8/18 branches; kernel 23/24 statements and 5/6 branches. These are parent-interpreter measurements across 42 pure fixture cases; CLI goldens run in separate processes and are not counted as covered lines. Remaining gaps include adapter/CLI paths and defensive invalid-state branches; B3 owns the expanded failure matrix. No blanket coverage claim.
