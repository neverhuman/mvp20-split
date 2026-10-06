# Graph Successor Admission

Design status: BP-04.04/B2 implementation boundary; predecessor graph semantics are accepted. Parent: [Graph Execution Model](Graph_Execution_Model.md).

## Authority and source cut

A successor is a new run of a separately compiled, reviewed plan. Its proposal names the predecessor run, exact predecessor plan digest/revision, new plan digest, fresh inputs and an explicit carried-state map. Human or autonomous topology changes use this boundary after the predecessor terminates. The predecessor's plan, history, inputs, outputs and receipts remain immutable.

Carry sources are a named final run export or a named output of one succeeded graph activation. The latter supports a retained checkpoint from a cancelled campaign. Runtime exposes a bounded source observation containing the current predecessor cut and exact value fingerprints; this is an observation, and admission rechecks it. Each mapping names its source, target input and expected fingerprint. Fingerprints use SHA-256 over canonical ASCII JSON `{"profile":"amphora-carried-value-v1","value":<fully serialized GraphValue>}`, with sorted keys and compact separators.

## Admission transaction

Use the existing global admission guard, then lock the scoped predecessor run. Require terminal status, the exact plan/revision cut, zero reserved invocation budget, no unsettled or leased/uncertain attempts, and no prepared completion/binding/wait retention intent. Transport notification delivery is separate from execution authority; it does not rewrite an accepted scientific result or bypass these checks.

Resolve carried values from committed owner state. Require a succeeded node for node-output sources, exact source fingerprints, unique target ports and no overlap with fresh inputs. Validate all resolved inputs against the successor's exact schema, representation, unit, collection/missing-slot and scope declarations; its compiled tool/checkpoint bindings retain their ordinary compatibility checks. Reuse ordinary graph admission for the active-campaign guard, limits, initial frontier, immutable plan lock and worker dispatch.

Persist the new run, explicit ancestry/mapping, source-cut transfer digest, admission audit and original command receipt in one transaction. A rejection creates no successor frontier or ancestry row. Exact command replay returns its original receipt even if later history advances. Concurrent successor proposals serialize under the existing single-active-campaign guard. New invocations receive new run-scoped identities; accepted predecessor work is carried as data.

## Ownership and replacement

The focused Runtime successor module owns source-cut resolution, readiness, transfer validation and ancestry reads. Graph admission owns creation of a run; Artifact retains ownership of immutable bytes and protection. No cross-owner database read, artifact network call, scientific transform or topology hot-swap occurs inside successor admission.

Add versioned public proposal/source/lineage roots without changing existing graph or worker schema bytes. An additive private migration makes ancestry insert/read-only for the service role and ties both sides to retained graph plans/runs and audit revisions. Replacement must preserve original source hashes, carried values, ancestry, plan locks and receipts. Tests cover running/stale/foreign predecessors, unsettled attempts, changed fingerprints, duplicate/incompatible targets, rollback/replay and subsequent execution. Source-derived continuation uses the existing retained-state Artifact and a newly authored loop graph; biological correctness and algorithmic evolution remain separate scopes.

## Newly validated draft successors

Runtime0.65 adds graph.admit_draft_successor through the separate draft_successor0.1 public contract. Its configured-only POST/v1/graph-runs/draft-successors route combines exact draft selection, current universe/Registry eligibility and predecessor cut/carry in the existing admission transaction. Terminal command replay precedes current eligibility checks; new admissions recheck both authorities. Draft publication and immutable lineage commit together with the run. Existing configured successor admission and published-plan execution lookup retain their original authority; no implicit admission of historical plans occurs. No migration is required. Planning topology proposal/compiler/handoff evidence remains separately owned by BP-08.04.
