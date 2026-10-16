# POP-01.04 Population contract decision

- Status: approved by owner 2026-10-13 18:45:57 America/Chicago; E1 implementation active.
- Reviewed: 2026-10-13 18:26:00 America/Chicago.
- Parent: [POP-01.01/E1](POP-01.01%20Population%20Execution.md).
- Baseline: `a614e594`; [activation inventory](../../Audits/POP-01_Activation.md).
- Implementation: E1=93.75%; D1-D3 complete; D4=75%; composition/resource/write-set review complete, resource admission decision open. This decision is part of E1, not a fourth weighted child.
- Owner direction: additive population profile and E1 contract/domain-validation/compatibility work approved. Existing profiles remain exact.
- Active interruption: none; owner confirmed LAN access and authorized continued implementation.
- Next gate: tested E1 schemas/goldens and concrete execution/write-set review before
  E2 activation. New public Runtime routes or graph primitives are not assumed needed.

## Why a new profile

The present search format embeds a population/checkpoint and one evaluator. Its
128-member population, 256-member selection and 262144-byte tool boundaries are
deliberate. Raising one limit would leave the other limits, replay and missing-fitness
semantics inconsistent. The new profile separates immutable scientific membership
from operational batching, while retaining the existing numerical algorithms and
Runtime execution authority.

## Proposed first profile and ownership

Add independently named public `population.*` schema roots in a focused public
contract package, with profile `numeric-population-v1` and closed wire version `1`.
Do not overload `search.*` version1 or automatically convert old checkpoints on read.
Graph-step DTOs remain a separate package from domain records. Numerical domain
objects stay with Search; DTOs validate/serialize and do not own behavior.

This first executable evolutionary profile is finite numerical search. Generic
candidate/material references permit later representations, but chemical variation
requires a separately registered operator and qualified profile. The supplied
chemical fixture remains a representation demonstration, not a numerical winner.

| Record / domain responsibility | Required retained identity and rules |
|---|---|
| Population specification | Scope/search revision, seed/RNG/operator pins, representation, objectives/units/directions, constraints/context/Knowledge pins, admitted method-graph digest, named method-to-node mapping, exact tool releases, assembly policy and all budgets |
| Candidate occurrence | Stable birth ID, representation reference/revision, ordered genetic parents, operator/draw interval and duplicate/rejection disposition; generation membership separate from birth |
| Evaluation key | Candidate/material revision, occurrence, named method, exact release, inputs/conditions/context and objective policy digests; retries are attempts under that key, not new observations |
| Generation manifest | Specification digest, generation0 or successor index, predecessor/checkpoint, ordered member/evaluation page references, row counts/digests and frozen observation cut |
| Terminal outcome | Exact evaluation key, accepted producer/output evidence or explicit failed/cancelled/unavailable/inapplicable disposition; missing is never a numeric score |
| Fitness assembly | Registered tool/policy maps named method evidence to ordered objective vector/units, constraint violation and per-objective provenance; Runtime routes rather than scores |
| Selection receipt | Complete declared parent/offspring union digest, eligible/excluded memberships/reasons, all ranks, survivor set, policy and stop/disposition; UI may not rerank |
| Proposed successor | Expected accepted predecessor, selection receipt, deterministic RNG state, offspring manifest and budget accounting; publication does not grant acceptance |

Use focused immutable domain objects/factories for identities, page validation,
membership, evaluation coverage, selection eligibility and successor consistency.
Canonical bytes use an explicitly named UTF-8 finite JSON profile and domain-separated
identity hashes. Existing search-json-v1 hashes and float behavior remain unchanged.
Record the new profile's exact ordering/number rules in tested goldens before use.

## Bounded pages and resource policy

Proposed first-profile maxima, enforced together rather than advertised as an
unrestricted Cartesian product:

| Dimension | Ceiling / interpretation |
|---|---|
| Population / global union | 1000 candidate slots; 2000 distinct parent-plus-offspring selection members |
| Methods / objectives / numeric dimensions | 8 named evaluation methods; 16 objectives; 32 numeric coordinates |
| Generations | Generation0 plus at most100 successor generations; smaller admitted total-work/deadline budget takes precedence |
| Fresh method evaluations | At most8000 per generation; declared union can retain at most16000 method outcomes including parent evidence |
| Artifact page | At most64 rows and131072 canonical bytes, whichever fills first; oversize row rejected before publication, never silently truncated |
| Manifest closure | At most512 page references and64MiB verified page bytes per generation; manifest itself <=262144 bytes; reject overflow explicitly |
| Individual row | <=8192 canonical bytes; large representation/evidence content remains an exact Artifact reference |
| Dispatch slice / active invokes | Configurable1..32 admitted work items per pass;1..8 active scientific invokes across the campaign, including nested method branches and orchestration tools |
| Total graph work | Existing100000-activation maximum and run deadline retained; count process/control/materialization nodes as well as evaluators before admission |
| History | Page default50/max100, explicit cursor/cut, no recursively embedded predecessor history; source authorization required on every read |

Pages are deterministic by canonical row order and exact serialized bytes. A generation
manifest names the complete closure; no implicit next-page discovery or unbounded
recursive fetching. Each page must match its declared scope/schema/hash/size/count;
duplicate, missing, reordered or foreign generation rows reject. Permissions and
retention are owner checks, not assertions in the JSON. Every reachable page required
for accepted history must be protected; protecting only the manifest is insufficient.

Maxima are engineering admission bounds awaiting E2/Q3 measurement. A1000-member,
100-generation,19-stage campaign can exceed the existing activation/deadline bounds
and must be rejected or explicitly reduced before launch. No automatic truncation
or undocumented expansion of the old Runtime ceiling is authorized.

## Selection and iteration policy

Freeze policy before dispatch. The default new profile waits for every required
evaluation to become terminal, then excludes a candidate whose required fitness is
unavailable. Keep each exclusion and original failure visible. Optional annotations
and weak-but-present admissible evidence do not automatically exclude candidates.
Hard execution prerequisites still govern whether a dependent tool can run.

Apply the existing constrained feasible-only Pareto/crowding ordering to the entire
eligible union, with stable ID tie breaking; never choose winners per dispatch page.
The default minimum is two distinct feasible parents, explicitly configurable in
the new specification from1 through requested survivor count. A population of1
must explicitly choose minimum1. If fewer are available, stop with
`insufficient_eligible_parents`; zero feasible members retains `no_feasible_survivors`.
If fewer than requested but at least the minimum survive, continue from that smaller
parent set and retain `insufficient_survivors` as a separate selection disposition.
Do not invent repeated survivors to fill the count or relax constraints after seeing
results. Zero evaluations, duplicate-only generations and budget exhaustion have
explicit deterministic stop/continuation rules in E1 goldens.

RNG consumption follows canonical candidate/offspring order, independent of network
completion or batch size. Preserve old counter-RNG and variation mathematics where
applicable; identities include the new profile/specification. Same-profile resume
requires original immutable pins. Changed Knowledge/tool/objectives use a successor
campaign and explicit re-evaluation/reuse policy. No human approval between waves.

## Scientific process composition

Keep material derivation separate from genetic ancestry. Introduce bounded public
process-state/derivation records for the synthetic qualification fixture: exact
input/output material revision references, named roles, conditions/units, provenance,
unknowns and tool binding. Up to32 consumed and32 produced references per transform;
each record obeys the same byte budget. Many-input reactions are not two-parent mating.
These records confer no real reaction, stoichiometry, safety or lab-control authority.

Required/optional ports remain explicit. Pairwise mapping requires equal cardinality
and declared order; keyed mapping requires unique keys and an explicit unmatched-key
disposition; Cartesian mapping requires an explicit opt-in and admitted output cap.
All mappings preserve candidate/generation/material-batch identity. A registered
mapping/transform tool can emit a bounded manifest for ordinary scatter. No join
is reinterpreted as a chemical operation. Repeated width changes and local dependency
readiness reuse existing graph scopes/control edges; visual columns are not barriers.

## Runtime transition/write-set requirement

Prefer composition from existing admission, Artifact projection/materialization,
scatter, iterate and worker acceptance. The current scatter already inserts a child
and updates its cursor under the same Runtime transaction. A page-based composition
must preserve that property and freeze the complete generation before its first
dispatch. Dispatch slices are operational; no page becomes a selection boundary.

E1 must produce an executable composition fixture plus a precise write-set map for:

1. Freeze generation: retain manifest closure, original specification/method/policy
   and expected predecessor before making any evaluation eligible.
2. Dispatch: under the run lock check active-invocation/activation/budget limits,
   insert deterministic work identity and advance its cursor atomically.
3. Accept result: existing worker fence/lease, producer/input/output binding,
   protected artifacts and unique terminal scientific evaluation identity.
4. Accept selection/successor: compare exact frozen coverage and predecessor, retain
   selection plus new manifest, then expose next-generation work in one transaction.

External Data I/O remains outside SQL transactions with durable preparation and
receipt reconciliation. Late results cannot rewrite closed generations. Physical
tool execution can repeat after failure; only accepted work is unique.

If existing primitives cannot express one of these transitions, E1 documents the
minimal generic Runtime extension, DTO/route, migration and rollback/replay behavior
for owner review before implementing that material extension. This approval does
not authorize an unspecified new command, generic code execution or a second runner.
U1 separately reviews population read APIs; E1 must not preempt their owner boundary.

## Ordered E1 delivery and acceptance

After approval, complete these prerequisites in order, with scoped tests beside each
owning module and publication through the existing generator:

1. Versioned records, domain identities/semantic validation and negative/golden
   vectors; full producer/consumer map including Search, Runtime, Research, Planning,
   Data, Registry/SDK and Studio. No default activation of the new profile.
2. Legacy schema-byte/receipt replay and numerical regression; original128/256/byte
   rejection oracles remain. Explicit new ranking entry leaves old guards intact.
3. Page size/hash/closure, method coverage, missing-fitness/minimum-parent, duplicate,
   RNG/batch independence and multi-stage mapping contract oracles.
4. Concrete graph composition/write sets and resource math; assess any minimal
   remaining public execution extension before E2. E1 is not complete at DTO delivery.

E2/E3/E4 still own actual dispatch, selection acceptance, crash/replacement and scoped
execution audit. U1-U4 and Q1-Q4 remain subsequent, unchanged gates. No new paid calls,
external data disclosure or scientific efficacy claim is part of this decision.
