# Numeric evolutionary search boundary

- Owner: BP-08.02/B1.02b verified; package0.4.0. Separate synthetic evaluator is B1.02c. BP-08.01 remains closed for its0.1.0 boundary.
- Scope: finite continuous numerical search primitives; independent Python implementation, not a verified v1 port.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); [activation](../../docs/Audits/BP-08.01_Activation.md).

CandidateScore owns finite objective/constraint values and an explicit eligibility flag. ObjectiveSpace owns direction, dimensional compatibility, bounded pairwise constrained dominance, Pareto front assignment and normalized crowding. Selection retains every candidate rank and distinguishes requested zero, empty feasible set, insufficient feasible membership and selected results. Unknown/ineligible fitness rejects the whole selection; it never becomes a favorable zero. Feasible-only survivor policy preserves infeasible ranks for explanation. No scientific acceptance follows from a numeric rank.

Input bounds: 1..256 uniquely identified candidates, 1..16 objective dimensions, finite float64 values, nonnegative finite violation, closed minimize/maximize directions. Lower violation dominates higher violation; equally infeasible candidates do not dominate one another through attractive objectives. Feasible Pareto comparison respects each direction. Crowding normalizes each nonconstant axis, uses an explicit boundary flag instead of JSON-incompatible infinity, scales differences to avoid overflow, and breaks ties by candidate ID. Constant axes add no crowding or arbitrary boundary preference. Input order cannot select a different tied candidate.

The numerical domain objects perform no I/O or global RNG access. The CLI and configured worker adapter use the public Tool Protocol SDK for Runtime/Artifact infrastructure only; they own no SQL, graph scheduling, model/source authority, molecular representation or evaluator. Public search/checkpoint DTOs, intrinsic consistency checks and seeded candidate state are implemented; graph-step/standalone worker integration belongs to BP-08.02. Existing synthetic solver tools remain unchanged.

Mathematical reference: [Deb et al., NSGA-II](https://ieeexplore.ieee.org/document/996017). No v1 or external source copied. Exact v1 pins/license observations and Lab placeholder disposition are in [reuse disposition](../../docs/Build%20Plans/BP-08/BP-08.01%20Reuse%20disposition.json). This is constrained Pareto/crowding selection with an explicit feasible-only policy, not a claim to reproduce the v1 SBX/mutation/RNG implementation or scientific benchmarks.

Rebuild acceptance: module-owned tests under tests/ranking cover independent fronts, objective direction, constraint precedence, stable ties, invalid/ineligible/mismatched data, extreme numeric ranges and bounded membership. Preserve result ordering/dispositions or publish a new policy version. Cross-platform or algorithm-performance claims require separate evidence.


## Original specification and portable random stream

OriginalSearch validates the public SearchSpec again at entry, rejects reversed bounds, duplicate coordinate/objective/implementation identities, blank units and cross-scope or duplicate context references. Its digest binds every original pin, including seed, budgets, evaluator and implementation versions. Resume requires a separately supplied original specification; a checkpoint cannot authorize its own replacement specification. Canonical search-json-v1 bytes are validated DTO JSON with sorted keys, compact separators, UTF-8/ensure_ascii=False, allow_nan=False and no trailing newline. This Python JSON profile is not an RFC 8785 claim.

CounterRandom is immutable. sha256-counter-u53-v1 hashes ASCII `amphora.search/sha256-counter-u53-v1` followed by one zero byte, the decoded 32-byte seed and an unsigned eight-byte big-endian counter. Take the first eight digest bytes as unsigned big-endian, shift right 11, then divide by 2^53. One draw advances the counter by one; the terminal safe-JSON counter 2^53-1 is serializable but cannot draw again. No global state, Python random internals or pickle is involved. Resume verifies the algorithm and original seed. NumericBox consumes one draw per coordinate, including fixed axes, interpolates low+(high-low)*u and clamps floating-point endpoint rounding.

Dependencies are the public search contract closure plus the Python standard library. Algorithm golden vectors were calculated independently using Windows .NET SHA256/UInt64. Tests live in tests/randomness and tests/specification; synthetic specification pins are fixture labels, not scientific authority. Cross-installation replay is verified; accepted predecessor-chain and generation-transition verification remain BP-08.02.


## Checkpoint mapping

CheckpointSnapshot validates intrinsic state against a separately supplied OriginalSearch: canonical attempt identities, seed replay, RNG intervals, generation/slot/population membership, duplicate ancestry, exact proposed-to-pending/terminal correspondence, request digests, evaluator/objective/unit/constraint/evidence scope, progress and phase/stop consistency. Selection receipts are recomputed from the frozen evaluated membership; unavailable fitness cannot enter ranking. Stable evaluation IDs are ev- plus the candidate digest. Candidate IDs hash compact JSON [numeric-attempt-v1, original-spec digest, generation, ordinal, operator, float.hex genes, parent IDs, draw start, draw end]; outcome disposition is retained separately. Selection membership hashes the sorted candidate-ID list as compact JSON.

encode/decode are pure transport mapping. They do not prove that evidence or predecessor Artifacts exist, have authorized access, or that a prior Runtime commit accepted a transition. Data/Runtime and BP-08.02 own those checks, predecessor-chain verification, generation transitions and actual tool dispatch. A snapshot with internally consistent pins does not authorize execution. One-attempt box variation is implemented; complete generation transition/replay remains in BP-08.02.

Tests/checkpoint independently constructs a zero-seed candidate, pending request and single-candidate rank, then mutates identities, scope, units, evaluator, budgets and receipts. Initial-state, duplicate/rejection and budget cases are verified; generation-transition failure/recovery belongs to BP-08.02.


## Initial numeric population

InitialPopulation.generate performs one bounded seeding step. It retains exactly population_size attempted samples and one RNG draw per axis per attempt. Unique samples become requests up to the evaluation budget; repeated genes refer to their earlier proposed attempt; budget-limited samples are retained as rejected/evaluation_budget. No request is sent. A zero evaluation budget produces a stopped checkpoint with every rejected attempt preserved. max_generations=0 still permits generation zero; no offspring generation is authorized by that value.

The returned request set is validated against all proposed attempts before exposure. Checkpoint mapping independently verifies initial-population completeness and duplicate/budget dispositions. Two separate Python processes reproduce identical canonical bytes for a 128-member fixture. This is process replay, not yet isolated installation or Runtime recovery.


B3 verified 2026-10-06 10:17:52:129 checks14.10s;426/438 statements and92/98 branches covered (96% combined). Malformed RNG/version/operator/pending identities, false stop reasons, forged ranks, missing attempts and duplicate targets reject. Seven frozen v1 source hashes match; no v1/Rust/Lab source copying or scientific claim. Remaining uncovered paths are future-generation ancestry/predecessor handling and the defensive ranking empty-front guard; generation transition/replay belongs to BP-08.02. Source audit tests/reuse requires the read-only workspace; installed algorithm tests exclude only that source audit.

Replacement verified 2026-10-06 10:22:13: two separately built wheel closures,133 tests each, identical wheel hashes and saved128-member checkpoint. Public JSON Schema consumer accepted the retained bytes; pending identities and the next RNG draw matched after replacement. No private service package, SQL or provider credential was available. [Installed proof](../../docs/Audits/Evidence/BP-08-Search/Installed.json); dev/verify_search_installations.py reproduces this bounded check. Different-version upgrades, target-host portability and accepted Runtime generation replay are separate gates.

## Graph-step binding and box variation

BoundCheckpoint binds an intrinsic snapshot to its exact canonical search.checkpoint Artifact digest, size, scope and schema. SearchStepContext supplies the separately pinned original specification. Equivalent noncanonical JSON is deliberately rejected rather than falsely verified against another byte stream. This pure check does not fetch or authorize the Artifact; Runtime/Data retain that authority. request_batch expands the frozen pending set into self-contained EvaluationRequests without dispatch. Graph-specific DTOs live in contracts/search_steps, separate from domain-neutral search DTOs.

BoxVariation performs one finite-box attempt using the original operator/seed pins and an explicitly ordered parent pool. Draw schedule: two uniform parent-index draws, one crossover decision, then blend, mutation decision and offset per axis. All3+3*d draws are consumed even when crossover/mutation is disabled or bounds are fixed. Blend is alpha*a+(1-alpha)*b; mutation adds (2*u-1)*fraction*(upper-lower), then clamps to the original bounds. Repeated chosen parent IDs collapse to one lineage entry. No selection, scheduling, implicit retry or generation loop is hidden in this operation.

Verified 2026-10-06 10:38:13:146 numeric/boundary checks16.32s; new binding/variation modules100% measured line/branch coverage, complete numeric module96%. Independent .NET draw values pin crossover and mutation/clamping cases. Public step publication40 checks19.23s;570 schemas, all564 predecessor bytes unchanged. Standalone adapters, generation state transitions and actual-owner recovery remain open; earlier133-test isolated proof applies to release0.1.0.

## Pure generation transitions

SuccessorPopulation opens exactly one successor from selected feasible parents; it retains parent observations, fixed-draw offspring ancestry, duplicate links and budget-limited rejections. GenerationReducer accepts the complete frozen pending set; duplicate/missing identities reject, returned observations are canonically ordered, and failed graph slots remain explicit unavailable outcomes. MissingValue.member_id must match the original scatter position. Late results cannot be applied to a selected/stopped generation. Stopped-state calls with no new results are no-ops.

Each changed checkpoint points to its bound source Artifact. These are pure proposed transitions; only Runtime may accept them. generations_completed counts resolved successor generations: an open/ready generation g reports max(0,g-1), while selected/stopped reports g. Generation zero does not count as a successor. This corrects the generation-zero-only prototype rule before integrated generation persistence exists; wire bytes/schema remain unchanged.

Stop order is no feasible survivors, generation budget, evaluation budget, then unchanged survivor-front objective vectors. Unavailable numeric fitness yields an explicit unavailable_fitness stop with every result retained; weak-but-present numeric evidence is not rejected merely for its provenance label. Frozen evaluator/objective/constraint pins still apply. Duplicate-only generations can select cached parent fitness without new evaluations and count toward the unchanged-front limit. No loop, network dispatch or database acceptance occurs in these domain objects.

Verified 2026-10-06 10:45:54:155 scoped checks17.21s;617/618 statements,133/134 branches covered (99% combined). Remaining gap: defensive empty-membership front helper. Actual owner/process recovery remains B2/B3; no deployed worker claim.

## Standalone capability modes

The package exposes four separately described operations: numeric.search-seed (SearchSpec to SearchCheckpoint), numeric.search-requests (SearchStepContext to EvaluationRequestBatch), numeric.search-collect (CollectedEvaluations to SearchCheckpoint), and numeric.search-vary (SearchStepContext to SearchCheckpoint). Each worker process is configured for exactly one operation and can be replicated independently. No sibling-tool implementation imports or hidden operation discovery are used.

`python -m amphora_evolution_search compute --operation seed --image-sha256 <pin>` consumes bounded JSON; describe emits the operation descriptor; schema emits its exact published validation schema; worker --operation <mode> --config <path> runs one Runtime-issued invocation via the existing SDK. Numerical checkpoints are ordinary immutable output Artifacts, not worker-attempt checkpoints; descriptors explicitly use pure/no-egress/synthetic-only and SDK checkpoint mode none.

The original specification must include ImplementationPin(name=numeric-search, version=current package release, sha256=configured image identity). Adapter execution is unavailable until descriptor binding supplies that identity, and an adapter cannot rebind to another image. CLI image arguments declare a fixture/deployment pin; they do not prove that an image was built. Actual registry/deployment/Runtime binding remains required.

Inputs and outputs are capped at262144 bytes; schema cardinalities alone do not guarantee fit. Invalid data yields a closed safe failure code without echoing payloads. Compute emits exact canonical checkpoint bytes, with no trailing newline, so redirected bytes retain their Artifact identity. Dockerfile is an offline-wheel recipe; no image build or target-host claim exists yet.

Verified 2026-10-06 10:54:14:169 checks24.87s; adapter/capability modules100% measured coverage. Full package94% because CLI subprocess lines are not attributed to the parent (37 CLI statements/14 branches); independent CLI seed/describe/schema and safe-error cases pass. Actual worker HTTP/owner recovery remains B2/B3.
