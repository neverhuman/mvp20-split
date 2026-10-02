# Knowledge Structural Authoring

- Status: BP-06.02/B1 pure domain behavior implemented; persistence and public authority pending.
- Owner: Knowledge; [authoring architecture](../../../../../docs/Architecture/Knowledge/Authoring.md).

Vocabulary validates unique type/predicate identities and declared endpoint types. Its fingerprint sorts set-like vocabulary collections while retaining descriptions and version. StructuralPolicy pins synthetic-only authority and bounded counts of complete historical entity/assertion/alias/retraction records; clients must name that exact configured policy. It never infers scientific acceptance from a predicate name or model confidence.

GraphState owns immutable EntityHistory and AssertionHistory and converts them into explicitly sorted DomainGraphContent/Snapshot records. Graph genesis has no published head; the first edit produces revision1. A subsequent edit requires its full observed head, matching semantic snapshot, log position, vocabulary and policy. No implicit rebase occurs. Ordered operations compute a new state; any failure leaves the original untouched. Canonical UTF-8 content excludes incidental timestamps; accepted-log identity is separate.

Entity creation cannot reuse IDs. Context revision requires the exact current predecessor, same identity/type/label, next revision and explicit supersedes. A merge requires current unmerged same-type identities, retains both histories and adds an attributable alias. Assertions keep their original endpoint references; resolution follows aliases without rewriting source meaning. Alias cycles fail. Explicit different contexts remain available instead of being collapsed by a merge.

Assertion creation cannot reuse an existing or retracted identity. Correction appends the exact next revision under the current nonretracted predecessor and retains original grounding/interpretation history. Retraction adds a tombstone; it never deletes or resurrects records. Active assertion selection keeps each identity's latest nonretracted revision, including incompatible assertions under distinct IDs. No averaging or automatic contradiction resolution is performed.

ReferencedInputs traverses the closed public DTO tree to collect exact artifacts, source revisions/spans, traces and Research refs. It rejects foreign scope/graph, inconsistent metadata under an identity, out-of-range source spans and bounded-reference overflow before any adapter I/O. This validates structure only: it does not check source bytes, current rights, trace/source association, Research existence or semantic support. The forthcoming public-peer validator must do those checks before recording an observation.

State/history constructors are private owner composition points, not untrusted snapshot loaders. State is built by applying validated edits from genesis; importing a client-supplied snapshot as trusted state is unsupported. No module operation authenticates a caller, commits state, executes a tool or contacts a model/provider. Tests name synthetic semantic oracles and failure isolation; actual authoritative transaction and process gates remain open.

Verification checkpoint:36 owner tests and36 independent installed-owner tests pass;26 authoring and10 replay cases. Combined measured coverage319/334 statements and124/140 branches; remaining defensive error branches are listed in the committed Domain_Replay evidence. No transaction or scientific-authority coverage is inferred from this pure suite.
