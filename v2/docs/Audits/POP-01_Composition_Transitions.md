# Population composition and transaction review

- Status: E1/D4 composition/resource/write-set review; resource command decision pending.
- Reviewed: 2026-10-13 22:34:04 America/Chicago.
- Owner: [Population Execution](../Build%20Plans/POP-01/POP-01.01%20Population%20Execution.md).
- Evidence: Runtime `tests/population_composition`; compiler-only synthetic adapters.

## Executable composition

The real v4 compiler accepts a seed invocation followed by a bounded generation
iteration. Its body contains a bounded slice iteration, full-cohort selection and
successor proposal. Each slice projects candidate references, scatters into the same
method graph, collects all terminal positions and retains the cursor/evidence state.
Candidate methods branch: A can start immediately; B waits for its preparation tool.
An all-terminal join preserves missing outcomes for the assembly tool. It does not
invent zero fitness. Final selection sees the declared whole cohort/parent union;
no slice chooses winners. Generation zero executes once; stopped variation must be
an explicit no-op with no RNG draw, enforced by its future adapter and existing domain.

A separate compiled nineteen-stage fixture narrows/widens with up to four required
input ports per transformation. Every consumed result has an explicit graph edge and
source binding. These tools combine material; a synchronization join never implies
chemical combination. Local readiness is represented directly without a universal
stage barrier. The fixture has no claim of chemical plausibility.

The fixture catalog is intentionally test-only: it proves existing control/conversion
primitives can express the topology. It is not an executable worker implementation,
registered image, exact public population-step adapter or runtime recovery proof.
E2 must replace these schemas with exact published request/response adapters and bind
declared occurrences to actual method activation paths. It must verify every page,
producer acceptance and required terminal position, not infer those from compilation.
Public step transport and semantic-domain proof remain separate D1/D3 evidence.

## Resource accounting

For this fixture, N is population size, B is slice size, S=ceil(N/B), T=G+1 is total
generations including generation zero. The independent expansion oracle counts:

- Graph nodes: `3 + T * (4 + 6*S + 7*N)`.
- Minimum worker attempts: `1 + T * (2 + 2*S + 4*N)`.
- Primary scientific method occurrences: `2*N*T`.

The four per-candidate worker calls are preparation, two methods and assembly. The
remaining calls include seed, slicing/collection, selection and variation. Graph
node counts also include control and Artifact conversions. Retrying a worker consumes
additional attempt budget without creating a new scientific evaluation identity.

For N12/G3, B1 costs643 nodes/297 minimum attempts, B8 costs403/217, B32 costs379/209.
Scientific occurrences stay96. For N1000/B32/G100,726799 nodes exceeds Runtime's
100000activation ceiling even though each specification field is individually valid.
Admission must reject this combination; no truncation or eager future-generation
materialization. These counts are fixture-specific, not a generic graph cost formula.
E2 must count actual bounded scatter/iteration/process expansion and retry allowance.

Artifact maxima also intersect. Per-generation supplied closure is limited to512
pages/64MiB, pages to64rows/131072bytes, rows to8192bytes; reference envelopes and
conversions have their own262144byte ceiling. Historical full-cohort evidence for
retained parents counts toward the source union and closure, not just the new cohort.
Up to101 source sets still cannot exceed16000 unique observations. Adapters must
preflight a conservative serialized envelope/closure budget and reject unsupported
combinations before scientific dispatch. Unexpected actual overflow stops explicitly;
it cannot silently omit evidence. No promise that1000members×8methods×all generations
fits every closure. Optimized parent evidence projections are a later named change
if required scale cannot fit; they cannot weaken source verification.

Scatter max_parallel limits child scopes. It does not enforce a campaign-wide
outstanding worker-attempt cap across multiple tools in each scope. The separate
[bounded admission decision](../Build%20Plans/POP-01/POP-01.05%20Bounded%20graph%20admission%20decision.md)
is required before E2 can claim the configured1/4/8 invocation limits.

## Owner transaction and failure map

| Transition | Authority and atomic write set | Interruption/replay obligation |
|---|---|---|
| Admit immutable campaign | Runtime admission guard; command identity, retained definition/plan, run input snapshot, graph limits, root frontier, audit/outbox and receipt | Exact replay returns prior run; artifact upload alone cannot admit a run |
| Freeze slice and expand member | Runtime coordinator under run transaction; frozen ordered membership/digest, child scope inputs/frontier and next_index | Cursor advance and child creation commit together; no acknowledged lost member |
| Claim tool work | Runtime run lock; attempt/fence, activation state, reserved budget, revision, audit and claim receipt | New resource profile must check reserved count under this lock; saturation cannot spend or issue a lease |
| Publish candidate/evidence pages | Tool proposes through Data public upload/finalization; immutable content and exact refs | Unaccepted uploads remain provisional; never interpret upload as selection or generation advancement |
| Accept scientific completion | Existing Runtime completion intent/reservation/fence protocol; accepted outputs and retention evidence, attempt settlement/budget and receipt | External Artifact calls stay outside SQL; prepared/uncertain attempts retain authority until owner reconciliation |
| Project/materialize graph data | Runtime Artifact-binding intent and source/output reservations; accepted output/logical receipt, retention proof, node state and audit | Durable prepared conversion reconciles publication; no scientific worker lease or attempt budget is charged |
| Collect terminal cohort | Runtime ordered missing/succeeded child results; Search verifies declared slots, resolutions, observations and full manifest closure | Missing required evidence is explicit exclusion, not zero; late completion cannot rewrite closed selection |
| Accept selection/successor | Ordinary Runtime tool completion retains exact selection/checkpoint/birth/manifest refs; iteration feedback consumes only accepted output | Expected predecessor/generation and full domain chain must validate; no independently mutable Search workflow ledger |
| Start next generation | Runtime completed-body feedback and next child scope/frontier creation in existing iteration transaction | RNG state is pinned by accepted checkpoint; crash resumes the same next generation, not fresh randomness |
| Expire/cancel/recover | Runtime settlement and stale-intent recovery update attempts/reservations once; retain immutable accepted history | Sweep globally across tool types; stale remote processes cannot regain acceptance through old fences |

Source owners: Runtime `coordinator/admission.py`, `expansion.py`, `storage.py`,
`lifecycle/claims.py`, `settlement.py`, `completion/recovery.py`, and the
`artifact_bindings` module contract. This is a source-grounded transition design,
not new PostgreSQL population acceptance. E2-E4 must inject failures at these exact
boundaries through public APIs and independently replaced owner/worker processes.

## Remaining gate

D4 has four bounded review units: compiled topology, resource accounting,
transaction/write-set map, and resolved resource admission contract. The first three
are reviewable here. The last needs owner direction under POP-01.04's reserved public
Runtime boundary. No new public command, route, mutable ledger or Runtime scheduling
implementation has been introduced by these fixtures. E2 remains0 until E1 closes.

Verification:13 compiler/resource tests plus4 ownership checks pass (workflow22381).
Ownership check found seven existing duplicate registrations in five nested aliases;
these now use their parent Runtime/Registry/SDK/dev owner with area selectors. Dev
coverage sources were preserved. This is a registry repair, not reopened UI scope.
