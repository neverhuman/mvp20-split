# Numeric evolutionary search boundary

- Source release0.9.0 adds the opt-in [population domain](src/amphora_evolution_search/population/README.md)
  specification/membership, candidate/evaluation identities and fitness/selection under POP-01.01/E1.
  Original select retains its256guard; explicit select_population supports up to2000
  with the same Pareto/crowding mathematics. Worker operations are unchanged.
  No0.9 Runtime/Registry deployment is claimed;
  the installed0.5 baseline and frozen demo remain independently pinned.

- Owner: BP-08.02; package 0.5.0. Current-release image, Registry, independent installation and actual-owner replacement/recovery checks passed 2026-10-06 12:46:43 (America/Chicago).
- Scope: finite continuous numerical search primitives; independent Python implementation, not a verified v1 port.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); [activation](../../docs/Audits/BP-08.01_Activation.md).

CandidateScore owns finite objective/constraint values and an explicit eligibility flag. ObjectiveSpace owns direction, dimensional compatibility, bounded pairwise constrained dominance, Pareto front assignment and normalized crowding. Selection retains every candidate rank and distinguishes requested zero, empty feasible set, insufficient feasible membership and selected results. Unknown/ineligible fitness rejects the whole selection; it never becomes a favorable zero. Feasible-only survivor policy preserves infeasible ranks for explanation. No scientific acceptance follows from a numeric rank.

Input bounds: 1..256 uniquely identified candidates, 1..16 objective dimensions, finite float64 values, nonnegative finite violation, closed minimize/maximize directions. Lower violation dominates higher violation; equally infeasible candidates do not dominate one another through attractive objectives. Feasible Pareto comparison respects each direction. Crowding normalizes each nonconstant axis, uses an explicit boundary flag instead of JSON-incompatible infinity, scales differences to avoid overflow, and breaks ties by candidate ID. Constant axes add no crowding or arbitrary boundary preference. Input order cannot select a different tied candidate.

The numerical domain objects perform no I/O or global RNG access. The CLI and configured worker adapter use the public Tool Protocol SDK for Runtime/Artifact infrastructure only; they own no SQL, graph scheduling, model/source authority, molecular representation or evaluator. Public search/checkpoint DTOs, intrinsic consistency checks and seeded candidate state are implemented; graph-step and standalone worker integration is verified under BP-08.02. Existing synthetic solver tools remain unchanged.

Mathematical reference: [Deb et al., NSGA-II](https://ieeexplore.ieee.org/document/996017). No v1 or external source copied. Exact v1 pins/license observations and Lab placeholder disposition are in [reuse disposition](../../docs/Build%20Plans/BP-08/BP-08.01%20Reuse%20disposition.json). This is constrained Pareto/crowding selection with an explicit feasible-only policy, not a claim to reproduce the v1 SBX/mutation/RNG implementation or scientific benchmarks.

Rebuild acceptance: module-owned tests under tests/ranking cover independent fronts, objective direction, constraint precedence, stable ties, invalid/ineligible/mismatched data, extreme numeric ranges and bounded membership. Preserve result ordering/dispositions or publish a new policy version. Cross-platform or algorithm-performance claims require separate evidence.


## Original specification and portable random stream

OriginalSearch validates the public SearchSpec again at entry, rejects reversed bounds, duplicate coordinate/objective/implementation identities, blank units and cross-scope or duplicate context references. Its digest binds every original pin, including seed, budgets, evaluator and implementation versions. Resume requires a separately supplied original specification; a checkpoint cannot authorize its own replacement specification. Canonical search-json-v1 bytes are validated DTO JSON with sorted keys, compact separators, UTF-8/ensure_ascii=False, allow_nan=False and no trailing newline. This Python JSON profile is not an RFC 8785 claim.

CounterRandom is immutable. sha256-counter-u53-v1 hashes ASCII `amphora.search/sha256-counter-u53-v1` followed by one zero byte, the decoded 32-byte seed and an unsigned eight-byte big-endian counter. Take the first eight digest bytes as unsigned big-endian, shift right 11, then divide by 2^53. One draw advances the counter by one; the terminal safe-JSON counter 2^53-1 is serializable but cannot draw again. No global state, Python random internals or pickle is involved. Resume verifies the algorithm and original seed. NumericBox consumes one draw per coordinate, including fixed axes, interpolates low+(high-low)*u and clamps floating-point endpoint rounding.

Pure-core dependencies are the public search contract closure and Python standard library; CLI/worker adapters additionally depend on public search_steps and Tool Protocol SDK contracts/clients. Algorithm golden vectors were calculated independently using Windows .NET SHA256/UInt64. Tests live in tests/randomness and tests/specification; synthetic specification pins are fixture labels, not scientific authority. Cross-installation replay is verified; accepted predecessor-chain and generation-transition evidence is recorded in BP-08.02.


## Checkpoint mapping

CheckpointSnapshot validates intrinsic state against a separately supplied OriginalSearch: canonical attempt identities, seed replay, RNG intervals, generation/slot/population membership, duplicate ancestry, exact proposed-to-pending/terminal correspondence, request digests, evaluator/objective/unit/constraint/evidence scope, progress and phase/stop consistency. Selection receipts are recomputed from the frozen evaluated membership; unavailable fitness cannot enter ranking. Stable evaluation IDs are ev- plus the candidate digest. Candidate IDs hash compact JSON [numeric-attempt-v1, original-spec digest, generation, ordinal, operator, float.hex genes, parent IDs, draw start, draw end]; outcome disposition is retained separately. Selection membership hashes the sorted candidate-ID list as compact JSON.

encode/decode are pure transport mapping. They do not prove that evidence or predecessor Artifacts exist, have authorized access, or that a prior Runtime commit accepted a transition. Data/Runtime and BP-08.02 own those checks, predecessor-chain verification, generation transitions and actual tool dispatch. A snapshot with internally consistent pins does not authorize execution. One-attempt box variation and complete generation transitions are implemented; actual-owner replay is verified separately from intrinsic mapping.

Tests/checkpoint independently constructs a zero-seed candidate, pending request and single-candidate rank, then mutates identities, scope, units, evaluator, budgets and receipts. Initial-state, duplicate/rejection and budget cases are verified; generation-transition failure/recovery has separate Runtime-owned acceptance evidence.


## Initial numeric population

InitialPopulation.generate performs one bounded seeding step. It retains exactly population_size attempted samples and one RNG draw per axis per attempt. Unique samples become requests up to the evaluation budget; repeated genes refer to their earlier proposed attempt; budget-limited samples are retained as rejected/evaluation_budget. No request is sent. A zero evaluation budget produces a stopped checkpoint with every rejected attempt preserved. max_generations=0 still permits generation zero; no offspring generation is authorized by that value.

The returned request set is validated against all proposed attempts before exposure. Checkpoint mapping independently verifies initial-population completeness and duplicate/budget dispositions. Two separate Python processes reproduce identical canonical bytes for a 128-member fixture. This test is process replay; separate isolated-installation and Runtime recovery checks establish those wider boundaries.

## Graph-step binding and box variation

BoundCheckpoint binds an intrinsic snapshot to its exact canonical search.checkpoint Artifact digest, size, scope and schema. SearchStepContext supplies the separately pinned original specification. Equivalent noncanonical JSON is deliberately rejected rather than falsely verified against another byte stream. This pure check does not fetch or authorize the Artifact; Runtime/Data retain that authority. request_batch expands the frozen pending set into self-contained EvaluationRequests without dispatch. Graph-specific DTOs live in contracts/search_steps, separate from domain-neutral search DTOs.

BoxVariation performs one finite-box attempt using the original operator/seed pins and an explicitly ordered parent pool. Draw schedule: two uniform parent-index draws, one crossover decision, then blend, mutation decision and offset per axis. All3+3*d draws are consumed even when crossover/mutation is disabled or bounds are fixed. Blend is alpha*a+(1-alpha)*b; mutation adds (2*u-1)*fraction*(upper-lower), then clamps to the original bounds. Repeated chosen parent IDs collapse to one lineage entry. No selection, scheduling, implicit retry or generation loop is hidden in this operation.

## Pure generation transitions

SuccessorPopulation opens exactly one successor from selected feasible parents; it retains parent observations, fixed-draw offspring ancestry, duplicate links and budget-limited rejections. GenerationReducer accepts the complete frozen pending set; duplicate/missing identities reject, returned observations are canonically ordered, and failed graph slots remain explicit unavailable outcomes. MissingValue.member_id must match the original scatter position. Late results cannot be applied to a selected/stopped generation. Stopped-state calls with no new results are no-ops.

Each changed checkpoint points to its bound source Artifact. These are pure proposed transitions; only Runtime may accept them. generations_completed counts resolved successor generations: an open/ready generation g reports max(0,g-1), while selected/stopped reports g. Generation zero does not count as a successor. This corrects the generation-zero-only prototype rule before integrated generation persistence exists; wire bytes/schema remain unchanged.

Stop order is no feasible survivors, generation budget, evaluation budget, then unchanged survivor-front objective vectors. Unavailable numeric fitness yields an explicit unavailable_fitness stop with every result retained; weak-but-present numeric evidence is not rejected merely for its provenance label. Frozen evaluator/objective/constraint pins still apply. Duplicate-only generations can select cached parent fitness without new evaluations and count toward the unchanged-front limit. No loop, network dispatch or database acceptance occurs in these domain objects.

## Standalone capability modes

The package exposes four separately described operations: numeric.search-seed (SearchSpec to SearchCheckpoint), numeric.search-requests (SearchStepContext to EvaluationRequestBatch), numeric.search-collect (CollectedEvaluations to SearchCheckpoint), and numeric.search-vary (SearchStepContext to SearchCheckpoint). Each worker process is configured for exactly one operation and can be replicated independently. No sibling-tool implementation imports or hidden operation discovery are used.

`python -m amphora_evolution_search compute --operation seed --image-sha256 <pin>` consumes bounded JSON; describe emits the operation descriptor; schema emits its exact published validation schema; worker --operation <mode> --config <path> runs one Runtime-issued invocation via the existing SDK. Numerical checkpoints are ordinary immutable output Artifacts, not worker-attempt checkpoints; descriptors explicitly use pure/no-egress/synthetic-only and SDK checkpoint mode none.

The original specification must include ImplementationPin(name=numeric-search, version=current package release, sha256=configured image identity). Adapter execution is unavailable until descriptor binding supplies that identity, and an adapter cannot rebind to another image. CLI image arguments declare a fixture/deployment pin; they do not prove that an image was built. Actual registry/deployment/Runtime binding remains required.

Inputs and outputs are capped at262144 bytes; schema cardinalities alone do not guarantee fit. Invalid data yields a closed safe failure code without echoing payloads. Compute emits exact canonical checkpoint bytes, with no trailing newline, so redirected bytes retain their Artifact identity. Dockerfile builds an independently verified offline Linux/amd64 image. Local Windows-hosted Linux/TLS deployment is qualified by BP-09.03; other target profiles remain unverified.

## Verification and replacement

Current numeric 0.5.0 passes 173 owned algorithm/contract tests in each of two clean independent wheel installations, with identical wheel closures, retained 128-member checkpoint/pending identities and next-draw replay. [Release qualification](../../docs/Audits/Evidence/BP-08-Search/Eligibility_Requalification.json) records 199 focused checks and current Linux image profiles/goldens. Source audit tests/reuse require the read-only baseline workspace and are the sole exclusion from isolated algorithm suites.

[Registry/replacement proof](../../docs/Audits/Evidence/BP-08-Search/Registry_Replacement.json) checks exact image descriptors and local wheel closure, all five Registry activations, real Runtime/Data APIs, concurrent evaluator workers, retained generations, replacement installations and interruption recovery. There are 15 accepted invocations and six evaluations per campaign. A killed vary attempt replays identical bytes under the next fence; its stale completion rejects. No scientific or target-host deployment claim follows.

Coverage is measured per scoped run: pure generation source 617/618 statements and 133/134 branches (99% combined); binding/variation and adapter/capability modules 100%. The defensive empty-front helper remains a unit gap. Full-package coverage was 94% in the CLI-adapter run because CLI subprocess statements/branches were not attributed to that parent; actual process acceptance does not supply a new coverage percentage. Owned suites cover ranking, randomness, specification, checkpoint, generations, capability and CLI boundaries. Preserve these oracles and immutable accepted history when replacing implementation; incompatible changes require versioned profiles/releases.

Verified 2026-10-06 19:54:31: BP-08.05 recovery/reconstruction acceptance preserves six checkpoint states under partial-evaluation failure and fresh Runtime. A separate test adapter uses public domain exports/SDK, and its exact source is qualified in a derived Linuxamd64 image. This is an adapter rebuild, not algorithm replacement. Changed evaluator pins require an explicit successor/new-search revision; prior fitness is historical only. See [recovery audit](../../docs/Audits/BP-08.05_Recovery_Closeout.md).

BP-09.03 target-host evidence: [integrated campaign](../../docs/Audits/Evidence/BP-09-Deployment/Owner_Context_Campaign.json) and [closeout](../../docs/Audits/BP-09.03_Integrated_Demo_Closeout.md). Actual retained15/6/3/15 synthetic execution is software evidence only; earlier BP-08 qualification limits remain historical.
