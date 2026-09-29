# Executable Campaign Wire Boundary

- Status: wire-v2 compiler/interpreter accepted in BP-04.01/.02; BP-04.03 adds separately versioned wire-v3 waits and compiler support. V3 execution remains gated.
- Public entry: `amphora_contracts_campaigns`; this folder is private package organization.
- Architecture: [Graph Execution Model](../../../../../docs/Architecture/System/Graph_Execution_Model.md).

`values.py` owns scalar/artifact/collection types and explicit sources. `predicates.py` owns finite comparison/Boolean syntax. `nodes.py` owns scoped invocation/control/state declarations. `plans.py` owns authored revisions, context pins, exact locks, normalized scope interfaces and occurrence paths. These DTOs validate/serialize boundaries; they do not evaluate expressions, compile, perform I/O, persist state or grant authority.

The executable root requires wire `2` and `deterministic-v1`. Legacy CampaignDefinition requires wire `1` and is never automatically converted. Schema bundles and fixtures remain separate; package 0.2.0 exposes both roots. Old schema bytes stay unchanged.

## Scope and Value Meaning

Ports name typed scalars, immutable artifacts with exact schema/representation/unit/media type, or bounded collections of scalar/artifact slots. Units use the same bounded strings as tool ports; there is no implicit conversion. Tool calls still consume/publish artifacts. Scalar bindings support control and do not synthesize scientific payloads. Initial pure tools use JSON; the value wire can describe other declared media types for later profiles.

`input` references the current scope. `output` references a local node port. Nested scopes receive explicit captures and cannot reach another scope by guessing a node name. `result` references a completed loop-body export and is permitted only in that loop's termination predicate. Constants are bounded scalars or artifact references, never executable expressions or mutable dictionary pointers. Predicate paths are finite property/index steps; the compiler must verify declared scalar type against hash-pinned JSON Schema.

Control edges and value bindings are separate. Each scope is a DAG; loops use explicit state/feedback rather than back edges. Compiler domain objects own uniqueness, references, routes, reachability, cycles, port/schema/unit matching, policy coherence and complexity checks. Intended compiler limits include sixteen nested scope/predicate levels and bounded total nodes. Wire validity alone proves none of those semantic rules.

All-collection waits for required terminal members and fails on required failure, with explicit skipped handling. Partial collection declares a minimum and all-terminal or deadline closure, retaining missing-slot reasons. First-arrival selection is not a policy. Scatter freezes membership/order; zero members may produce an empty all-collection. Loops declare initial state and feedback exports, evaluate `until` after body commit, and always stop at the iteration limit with declared finish/blocked disposition. Actual transitions remain Runtime work.

## Immutable Products and Replacement

PlanLock binds normalized definition, compiler profile, exact tool LockEntry objects, schema identities and context pins. Context pins do not grant scientific authority or imply retrieval occurred. Mutable replica addresses/capacity expiry are not scientific lock identity; fresh resolver/admission checks remain necessary.

ExecutionPlan.sha256 covers canonical PlanDocument bytes, excluding the envelope's own hash. The document retains normalized definition, lock, scope order and inferred node interfaces. Definition identity uses the `amphora-executable-definition-v2` profile. Compiler/domain objects must verify hashes and semantic consistency; a syntactically valid digest is not proof. Layout is outside the semantic document.

ActivationPath distinguishes a local node and ordered loop/scatter occurrences; scatter also pins membership digest. It does not grant a lease or replace attempt fencing. Tools cannot advance iteration or adopt plans. Human/topology changes use a later campaign.

Owned tests: `contracts/campaigns/tests/executable/`; manual fixtures: `contracts/fixtures/v2`. The plan fixture is a wire example, not compiler evidence. Replacement preserves explicit version/scope/binding meaning and fixtures. Intentional changes require compatibility/consumer proof. No service/database/model/scientific authority belongs in this package.
