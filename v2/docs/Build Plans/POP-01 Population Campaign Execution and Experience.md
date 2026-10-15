# POP-01 Population Campaign Execution and Experience

Current E2.2 checkpoint: Search0.23 loop affinity qualified (386 source/384 installed; actual repeated loop normal/failure, pools27/28, selected16, truthful exclusion0/1). Paired-method collection/fitness also qualified; registered synthetic material/mapping workers next. Percentages unchanged.

## Canonical tracker

- Status: active POP-01.01/E2 bounded dispatch; before ML-01.
- Last refreshed: 2026-10-15 17:49:00 (America/Chicago).
- Scope revision: POP-01.04 and POP-01.05 approved; E1 complete, E2 active.
- Overall implementation: 10.42%; Execution31.25%, Experience0%, Qualification0%.
  Three equally weighted children, each with four equal delivery gates. Parent
  counts the twelve child gates once; Build15.63% is the first two children, Verification0%
  is the third. Planning/design maturity is separate from implementation.
- Owner: cross-owner population workflow; responsibilities assigned below.
- Prerequisite: UI-01/V1 and UI-02/P4 prove actual Knowledge, inventory-grounded
  LLM graph curation/missing-capability requests, browser Run and candidate detail.
- Current task: E2.2 registered synthetic material/mapping workers; paired methods, loop affinity and preceding components qualified.
  Full worker unit and authored composition/matrix remain incomplete. E1/E2.1 remain complete.
- Design readiness: POP-01.04 contracts/selection policy approved. New public Runtime
  extensions, if needed, still require concrete E1 review before implementation.
- Demonstrated behavior: BP-08 numeric evolution/recovery exists; the current
  two-candidate scientific demo does not demonstrate population-scale integration.
- Current gate: Complete E2.2 worker integration/qualification after approved POP-01.06. Later read-model ownership
  and actual version compatibility remain separate gates. No scientific dataset needed
  for deterministic engineering qualification. Actual polymer operators are separate.
- Acceptance: actual owner/process/browser proof, including restart and scale;
  no blanket human approval gate between generations.
- Activation audit: [corrected_ready for E1 design](../Audits/POP-01_Activation.md),
  2026-10-13 18:26:00; source inventory and37legacy checks pass. New contracts approved 2026-10-13 18:45:57; design earns no implementation credit. v1/completed plans stay closed.
- Active exception: isolated pop01-retention-integration worktree; original review source remains frozen while local15a/LAN15b serve. No merge/promotion until owner finishes review and wrappers drain. UI-01/V1 and UI-02/P4 prerequisites complete.

## Sequence and immediate children

| Child / parent phase | Completion | Prerequisite | Delivery |
|---|---:|---|---|
| [POP-01.01 Population Execution](POP-01.01%20Population%20Execution.md) / Execution | 31.25%; E1=100%, E2=25%, E3/E4=0% | Entry gate above | Explicit population/evaluation identities, bounded dispatch, global selection and durable recovery |
| [POP-01.02 Population Experience](POP-01.02%20Population%20Experience.md) / Experience | 0%; U1-U4=0% | POP-01.01 complete | Bounded authoritative projections, stable method graph, generation navigation and population comparison |
| [POP-01.03 Qualification](POP-01.03%20Population%20Qualification.md) / Qualification | 0%; Q1-Q4=0% | POP-01.02 complete | Fresh UI-started evolutionary campaigns, restart/failure/scale proof and ML-01 handoff |

Do not replace the near-term demo work with this plan. After its entry gate, POP-01
takes precedence over inherited-model migration. ML-01 starts only after POP-01
qualification; missing ML data cannot block the population engineering proof.
LR-01/UI-R01 may interrupt only when their failures block the current task, with
an exact return point. No calendar deadline is assigned to this tranche yet.

## The user experience being built

The main canvas shows the campaign's reusable scientific method, for example:

```text
Seed population -> evaluate each candidate -> assemble objectives -> select -> vary
                         | solvency |                            |          |
                         | viscosity|                            +-- next generation
                         | ...      |                                  or stop
```

The drawing is conceptual; rendered edges must come from an admitted authored graph,
not from this diagram or inferred names. Evaluation methods remain independently
selectable scientific steps, not one opaque Evaluate box. Multiple candidates share
that method; individual activation identities remain available underneath it.

A separate generation strip and population workspace answer: which population is
being evaluated, how many candidates are pending/complete/eligible, what survived,
what changed and why. Selected candidate details reuse UI-02's formula/structure
inspector. Deep execution detail is available without flooding the main graph.

## Four identities that must stay distinct

Owner addition2026-10-08 20:58:22: scientific process topology may repeatedly widen,
converge and widen again across19 or more stages. This is independent of population
fan-out and selection. [Multistage process semantics](../Architecture/Campaigns/Multistage_Process_Graphs.md)
defines multi-input/output tools, typed mixture/intermediate states, many-to-many
material lineage, local readiness and cardinality bounds. Each child below includes
the corresponding contract/execution/UI/qualification tasks; all remain0%.

| Concept | Meaning / authority |
|---|---|
| Campaign method graph | Versioned authored scientific/control/dataflow structure; Runtime admission authority |
| Generation | Frozen candidate cohort plus selection/evaluation policy and evidence; Search proposes transitions, Runtime accepts them |
| Dispatch batch | Operational slice of a generation's evaluation requests; not a generation or independent selection pool |
| Activation/attempt | Actual node execution and retries for a candidate/method/occurrence; Runtime retains authoritative history |

A generation contains candidate memberships, not copies of a whole authored graph.
The UI aggregates concrete occurrences, not execution authority. A graph-template
node, candidate membership and retry attempt each retain separate stable keys.
Scientific equivalence is not inferred from a similar structure or candidate label.

## Source-grounded reuse and gaps

Reviewed at planning time:

- `tools/evolution_search/README.md`: existing constrained Pareto/crowding selection,
  deterministic seed/variation, generation reducer, stopped states and predecessor
  checkpoint validation. This is an independent numeric implementation, not a
  verified extraction of v1 SBX/mutation. Do not rewrite it without a measured gap.
- `contracts/search/src/amphora_contracts_search/specification.py`: population cap
  **128**; checkpoint retains at most **256** current/parent attempts. These are
  different limits. Selection ranks, pending/observation arrays and byte ceilings
  must all be audited before increasing either.
- `contracts/search_steps/README.md`: request batch and full terminal collection;
  current reducer stops on unavailable fitness. Partial selection is a policy change.
- Search tool request/output cap **262144 bytes**. Raising population_size alone
  cannot establish scale. Historical receipts/checkpoints must keep their exact bytes.
- Runtime already owns scatter/iterate, leases, acceptance and recovery. Its graph
  navigation uses snapshot-bound pages of at most100 nodes and per-scope topology;
  it is not a population-wide result index.
- `studio/src/page_models/campaign_flow/README.md`: current connected demo loads at
  most32 root activations and has fixed method/candidate bindings. That is a bounded
  demo consumer, not a scalable population loader.
- Closed BP-08 and its recovery audit prove earlier bounded numeric evolution.
  `dev/local_numeric_campaign.py` still uses test/compiler fixtures for setup; the
  new production UI path must use supported public draft/validation/admission APIs.

## Ownership and exclusions

Search tools own candidate generation, ranking/selection and proposed checkpoints.
Domain representation tools own legal numeric/formulation/polymer/biological operators;
no generic mutation of molecular strings. Runtime owns all dispatch, retry/fence,
budget and accepted graph/checkpoint transitions. Data owns immutable pages/artifacts.
Research owns semantic evaluation/comparison eligibility and derived population
projections. Registry owns tool releases. Planning consumes bounded inventory and
evidence to propose future graphs. Studio owns selection, layout and presentation.

No second population scheduler, generic backend, private cross-owner imports or
scientific ranking in Studio. No second authoritative run database in Research.
Read projections may be rebuilt from accepted source records; any materialized
cache records its source cut and invalidation rule.

Human changes apply between campaigns. Generation progression is autonomous under
the admitted policy. Ordinary generations do not invoke the LLM per candidate;
any optional model checkpoint must be explicitly budgeted and separately qualified.
Changing tool, Knowledge, objective or comparison policy starts an explicit successor
context, not a silent rewrite of old fitness. Prior scores do not become comparable
merely because candidate IDs match.

## Scale and success boundary

First preserve/replay the old128-population profile. Then qualify a versioned
reference-backed profile at **1000 candidate slots per generation**, including
up to2000 parent-plus-offspring selection members, with configurable bounded batches
and in-flight work. Historical generations must not accumulate inside one growing
JSON checkpoint. These are planned engineering limits, not current capability.

Mandatory proof spans multiple generations, independent evaluator branches, varied
completion order, failures and restart. A large static canvas fixture is only UI
load evidence. Deterministic objectives can prove selection/orchestration; they
cannot establish viable polymers, scientific improvement or ML accuracy. A chemical
representation fixture exercises UI-02 identity/formula links without claiming that
numeric test mutations generated useful new molecules.

Do not lose the eventual polymer-generation dependency: qualify a representation-
specific generation/variation tool before claiming evolution of new chemical
structures. POP-01 records that missing capability through the established LLM
request mechanism and hands it to ML-01/M1 for a named implementation disposition
or separately scoped tool plan. Parameter evolution, catalog selection and novel
molecular generation must remain visibly different modes. A model adapter alone
does not fulfill a chemistry-generation request.

## Closeout

Each child owns module tests and component drift review; parent Q4 closes the
cross-owner audit, updates module replacement READMEs/inventories and transfers
explicit limits to ML-01. Keep a POP-01 History.md when implementation starts to
record checkpoints and scope decisions; do not expand this tracker into a log.
