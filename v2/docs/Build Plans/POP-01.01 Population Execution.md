# POP-01.01 Population Execution

- Status: queued; parent [POP-01](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md).
- Last refreshed: 2026-10-08 20:19:11 (America/Chicago).
- Implementation: 0%; E1/E2/E3/E4=0%, four equal delivery gates.
- Prerequisite: parent entry gate. Current task: none; next E1.
- Owners: public contracts, Search tools, Runtime scheduling/acceptance, Data artifacts,
  Research evidence eligibility. No implementation credited for this design.
- Exit: independently installed versioned population execution and recovery work
  through public graph APIs; semantic selection cannot depend on dispatch batch order.
- Blockers: schema/version and authority decisions listed in E1. Acceptance pending.

## E1: inventory, semantic contracts and compatibility

Reconcile actual source/schema/receipt behavior against BP-08 before changing it.
Publish a bounded decision record plus tested DTOs/goldens; preserve v1 wire bytes
and numerical outcomes. A new profile/version is required for larger/reference-backed
populations, multiple evaluation methods or changed missing-fitness policy. Never
silently relax old cardinality, selection-rank, payload or same-checkpoint resume rules.
Review the concrete material contract changes under AGENTS before implementing them.

Objects to define behind boundary DTOs:

- Population identity: scope, run/search/specification revision, generation index,
  predecessor/checkpoint, immutable membership-manifest digest and policy pins.
- Candidate occurrence: birth attempt, representation revision/artifact, parent IDs,
  operator/RNG draw interval, and distinct generation membership. Retained survivors
  preserve identity; duplicate offspring retain their own disposition and source link.
- Evaluation key: candidate/material revision, method/release, input/context digest,
  conditions/units, objective/constraint revision and occurrence. Attempt IDs are
  separate; a retry cannot create a second scientific observation or budget-free call.
- Generation manifest: ordered, hashed immutable membership/evaluation pages and
  counts; selection pool explicitly includes intended parents and offspring. Page
  ordering and digests determine replay, not network arrival or filesystem ordering.
- Batch/work cursor: frozen evaluation membership, page/offset, policy and limits;
  deterministic keys allow dispatch replay without duplicate accepted work.
- Selection receipt: all eligible/excluded members, reasons, objective/rank/crowding
  policy, survivor membership and exact observation cut. No ranking from a UI page.

Proposed maximum first-profile population1000, union selection pool2000; small
artifact pages bounded by both member count and serialized bytes. Define maxima
for methods, generations, outstanding activations, history lookup and artifact size
before activation. New public routes/commands are specified only where current
draft/admission/scatter/iteration/Artifact primitives cannot implement these semantics.
Record producer/consumer/migration inventory and how old runs remain readable.

Exit: schema/negative/golden tests, compatibility report, transition/write-set
specification and reviewed contract decision; no generated-schema edits by hand.

## E2: bounded evaluation dispatch and deterministic collection

The authored campaign owns seed -> evaluation subgraph -> collect/select -> variation
-> next generation. Per-candidate evaluation may branch into named scientific methods
with dependencies; global constraints/data-preparation remain graph nodes, not copies
per candidate. Bind authored method IDs to concrete occurrences explicitly.
A declared fitness-assembly tool maps the required method outputs to a typed
objective vector with per-objective evidence/units and missing-outcome dispositions.
Runtime routes and accepts it; it does not implement chemical aggregation or scoring.
The single-evaluator legacy contract cannot silently become a multi-method context.

Runtime schedules immutable pending work using configured worker/tool/resource limits.
Separate batch size, active invocation count, candidate count and attempt count.
Changing dispatch batch size cannot change the seed stream, candidate membership,
global ranking or selected successors for equivalent deterministic results.
Do not materialize every future generation or enqueue an unbounded scatter at once.
Graph expansion and invocation/attempt budgets must include seed/collect/variation,
multiple evaluator calls and retries, not just population size.

Use existing claim/lease/fence/retention semantics. Persist the work cursor and
activation creation under Runtime's existing transaction authority; no acknowledged
cursor advance without durable admitted work. Accepted results bind exact input,
method and output artifacts. A network timeout means reconcile, not assume failure.

Freeze a generation before dispatch. Each terminal evaluation has one explicit
outcome; completion order does not alter RNG draws or canonical observation order.
Method failures are not zero objectives. Distinguish an optional missing annotation
from a missing objective, hard execution prerequisite or measured infeasibility.

Exit: actual public-owner run with simultaneous evaluator branches, batch sizes
1/8/32, in-flight limits1/4/8 and identical semantic outcomes; compare fingerprints
excluding execution-specific IDs/timestamps. Prove bounded admission at saturation.

## E3: generation policy, global selection and next wave

First release uses a generational barrier: every frozen required evaluation must be
terminal, including exhausted retries/cancellation, before the generation closes.
No selection of the first N fast candidates. A predeclared timeout can terminalize
work under owner policy; late results cannot rewrite a closed selection.

Keep legacy all-required-fitness stop behavior for old profiles. For the new profile,
define an explicit policy for excluding candidates with unavailable required fitness,
minimum eligible parent count and insufficient-feasible disposition. The default
must be frozen in E1, never chosen after seeing results. Exclusion preserves errors
and uncertainty; low-confidence but present admissible evidence is not automatically
an exclusion. Below the required parent count, stop with an actionable explanation;
do not fabricate scores, endlessly resample, or force an unapproved relaxation.

Apply constrained Pareto/crowding selection to the entire declared union pool.
Taking top candidates from each dispatch batch is NOT equivalent and is forbidden.
Use a bounded single Search invocation over validated page references for the first
2000-member pool; measure memory and algorithm cost before claiming scale. Any
different approximate/distributed algorithm requires its own named policy/evidence.

Search returns proposed immutable checkpoint/selection/offspring artifacts. Runtime
accepts the transition once against the expected predecessor revision and retains
its artifact pins atomically with graph progression; artifact upload alone is not
acceptance. Crash-created unreferenced artifacts are not selected populations.
Generation-zero versus offspring-generation counts must remain explicit.

Stop policies: generation/evaluation/attempt/cost/deadline ceilings, insufficient
eligible parents, no feasible survivors and declared stagnation. Never promise
monotonic scientific improvement. Separate natural stop, failed execution and user
termination. Resume the same profile without changing pins; changed Knowledge/tool/
objectives use a successor campaign with explicit re-evaluation/reuse eligibility.

Exit: independent global-selection oracle including ties, duplicates, constraints,
mixed objective directions, optional missing data and required unavailable fitness;
tests prove incomplete pools and post-close results cannot alter survivor decisions.

## E4: durability, replacement and execution closeout

Inject interruption before/after dispatch commit, result upload/retention, selection
artifact publication/acceptance, and next-generation creation. Replace worker and
Runtime processes independently. Resume exactly the remaining work; preserve RNG,
candidate ancestry, accepted artifacts, budgets and winner fences. Equivalent
uninterrupted and resumed deterministic searches have identical semantic checkpoints.
Retries can consume real resources even when acceptance is unique; no exactly-once
physical-execution claim. Scientific side-effect tools retain their own protocols.

Research may reuse prior fitness only under existing explicit representation,
context/evaluator and applicability rules; identical gene vectors alone are insufficient.
Invalidate reuse when any required pin differs. Retain the original evidence source.

Tests: Search randomness/ranking/transition suites; Runtime population scheduling,
transaction/concurrency/recovery suites using real PostgreSQL; artifact bounds and
SDK worker protocol suites; independent installs and legacy replay goldens. Register
the actual suite paths in dev/test_scopes.json. No single E2E test substitutes for
these boundaries. Update owning READMEs and scoped drift audit before child closeout.
