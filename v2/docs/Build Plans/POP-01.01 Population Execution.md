# POP-01.01 Population Execution

- Status: active E2; parent [POP-01](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md).
- Last refreshed: 2026-10-14 21:22:00 (America/Chicago).
- Implementation: 31.25%; E1=100%, E2=25%, E3/E4=0%, four equal delivery gates.
- Current: E2.1 bounded admission/capacity/recovery complete; E2.2 population step worker execution.
- Next: bind population step records to independently installed tools, then authored bounded collection.
- Approval: [POP-01.04](POP-01.04%20Population%20contract%20decision.md) approved.
- Evidence:356 source checks plus corrected two-test publication rerun/guard PASS;740schema pins unchanged.
  Search0.12 two isolated335test installs and legacy replay/wheels pass. Pure checks are not runtime admission.
- Owners: public contracts, Search domain, Runtime acceptance/dispatch, Data artifacts,
  Research eligibility. E2 starts only after the whole E1 gate passes.
- Gate: E1 passed:16 source and16 independently installed contract tests,99 legacy
  contract tests,30 publication tests and boundary guard.744 schemas;740 old bytes pinned.
  E2=25%: first bounded unit qualified; full population acceptance remains pending.
- Active exception: none. RG-01 placeholder planning interruption complete; owner places it after POP-01.
  Review wrappers remain drained before edits.
- Exit: independent versioned population execution/recovery through public graph APIs;
  selection cannot depend on dispatch order. Actual acceptance remains E2-E4.

### E1 delivery accounting

Four equal deliveries refine the existing E1 gate. D1 accounting now explicitly
includes ten equal units: eight record/domain families (specification, membership,
birth, evaluation, fitness, selection, successor, material lineage), producer/consumer
map, and graph-step transport. All ten are source-verified; D1=100%.
This corrects the earlier record-only denominator, which omitted two already-scoped
D1 exits; it adds no scope or acceptance credit. [Owner map](../Audits/POP-01_E1_Contracts.md).
E1=(100+100+100+100)/4=100%; Execution=100/4=25%.

| Delivery | Completion | Remaining exit |
|---|---:|---|
| D1 records/domain invariants | 100% | Complete; actual owner acceptance remains E2-E4 |
| D2 compatibility and numerical policy | 100% | Complete; [policy/compatibility report](../Audits/POP-01_Numerical_Compatibility.md) |
| D3 semantic/negative qualification | 100% | Complete; [semantic report](../Audits/POP-01_Semantic_Qualification.md) |
| D4 composition and write sets | 100% | Composition/resource/write-set review plus approved, independently installed additive contract |

D4 four equal review units: compiled topology, resource accounting, transaction/write
sets, resolved admission contract. All four complete (13 compiler/resource checks;
4 test-ownership checks). [Transition review](../Audits/POP-01_Composition_Transitions.md).
[POP-01.05 decision](POP-01.05%20Bounded%20graph%20admission%20decision.md) is approved; publication,740 predecessor pins and independent seven-wheel install pass.
This refines existing D4 scope, not a new dependent implementation phase.

Detailed checkpoints belong to [POP-01 History](POP-01%20History.md).

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

E2 delivery accounting refines this existing phase into four equal units, without
adding scope or resetting E1: E2.1 generic resource admission/claim/recovery25%;
E2.2 population step workers25%; E2.3 authored dispatch/collection composition25%;
E2.4 actual public-owner batch1/8/32 and cap1/4/8 qualification25%.
E2.1 is100%, E2.2-E2.4=0%; E2=25%. [Capacity milestone evidence](../Audits/POP-01_Bounded_Admission.md):
243 source checks,21 independent installed Runtime checks, actual HTTP restart and
independent Deployment preflight against qualified0.68 and unqualified0.67 pass.
No full population or performance claim follows from the generic capacity milestone.


E1 must also freeze multi-stage process semantics: multi-input/output ports, typed
material/intermediate revisions, required versus optional dependencies, explicit
pairwise/keyed/Cartesian collection policies and output cardinality bounds. Record
where existing graph constructs suffice versus where a versioned contract is needed.
Do not overload numeric genetic ancestry (currently at most two parents) as reaction
lineage. A control join waits; an actual registered scientific tool combines inputs.

E2 execution must support repeated widening/convergence and unequal branch lengths
inside a candidate process. Dispatch when local dependencies are accepted, without
a global stage barrier. Pin all precursor states and process inputs; never cross-wire
different candidates/generations/material batches. Accepted intermediate manifests
can expand downstream work only within declared cardinality/resource budgets.
Restart or downstream failure preserves prior accepted intermediates. Real material
conservation/reaction feasibility remains a domain-tool result, not a Runtime inference.

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
