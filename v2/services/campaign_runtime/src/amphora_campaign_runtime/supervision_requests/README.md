# Runtime supervisor request binding

- Owner: Runtime BP-07.04/B1.02a; Runtime0.22;62 scoped/wire/predecessor/publication cases pass;54 statements/4 branches100%. Independent combined exchange proof remains B1.02c.
- Architecture: [Graph Runner](../../../../../docs/Architecture/System/Graph_Runner.md).
- Public transport: contracts/supervision; [exchange design](../../../../../docs/Build%20Plans/BP-07/BP-07.04%20Supervisor%20exchange%20contracts.md).

ScopeExport produces a public SupervisionSnapshot from an owned DecisionFootprint, including exact original cut and selected view/state/output fingerprints. It delegates footprint/relevant hashes to supervision_scope rather than introducing another algorithm. Received hashes do not prove stored Runtime state.

SupervisionRequestBinding.bind requires exact snapshot equality with that original footprint, scoped run/reference, Planning actor/purpose/cut/scope/policy and artifact scopes, established UTF-8 Planning request hash and bounded lineage shape. Initial ordinal1 has no self/root/parent hash; ordinal2 must name the same root and parent. Later ancestors and aggregate budgets require stored owner validation. Both original Planning bytes and the full supervisor record are capped256KiB. Immutable canonical bytes and SHA256 preserve exact public request replay; this is not a command receipt.

This factory does not authenticate the caller, read current SQL/rights, prove stored-plan membership or absence of worker materialization, validate admitted policy contents, execute Planning ContextPolicy, establish an actual ancestry chain, check wall-clock expiry, reserve/settle spend or accept a decision. Those checks remain explicit prerequisites in owning journal/transport/acceptance phases. Constructing the dataclass directly or reparsing a record is not fresh validation authority.

Tests belong under tests/supervision_requests; public wire tests belong to contracts/supervision/tests. Literal Planning request bytes must remain compatible, and public snapshot digests must match the existing Runtime domain. Changed identity, actor/cut, hash, policy and lineage cases reject. Response/receipt/command profiles remain B1.02b; no HTTP host or model adapter exists here.
