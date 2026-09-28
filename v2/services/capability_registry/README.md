# Capability Registry

- Status: BP-03.01 immutable descriptor identity, semantic validation and pure selection policy implemented; no HTTP hosting, durable registration, deployment inventory or runtime routing yet.
- Package: `amphora-capability-registry` 0.1.0.
- Architecture: [Catalog](../../docs/Architecture/Capabilities/Catalog.md), [Tool Services](../../docs/Architecture/Capabilities/Tool_Services.md).

This owner will maintain the tool/node index. Its current [descriptor module](src/amphora_capability_registry/descriptors/README.md) binds immutable release identity, canonical metadata bytes, image/schema pins and explicit LockEntry verification. It imports only public core/tools contracts; it does not import runtime/artifact implementations, access peer tables or dispatch work. No import starts a process or network connection.

The new ReleaseDescriptor is a separate wire-v1 root containing the existing ToolDescriptor plus explicit resource/egress/checkpoint/reproducibility metadata and a restricted authority ceiling. Old ToolDescriptor, Invocation and Completion schemas and command fixtures remain unchanged. Release identity differs from deployment/replica identity; health never grants scientific eligibility or execution authority.

No authoritative registration success can be produced by this package yet. The immutable registration comparison is an owner domain precondition; BP-03.02 must apply it within the durable, authenticated registration transaction. Pure policy separates descriptor consistency, scientific suitability, scope/port/resource/permission compatibility and observed capacity. Later children own store/routing, SDK/tools and replica acceptance.

Tests belong to `tests/descriptors/`; run `dev/run_tests.py --module registry --area descriptors --coverage`. Coverage measures all current registry source; independent builds must contain neither peer service nor scientific packages. A replacement preserves canonical release profile, exact byte comparison under existing identity, full LockEntry matching and old execution wire compatibility. Preserve durable registration history once implemented; do not substitute healthy capacity for release suitability. Synthetic numeric/sequence fixture metadata establishes no chemical or biological validity.

B2 verification: 40 owner identity/policy cases measured 94% combined line/branch coverage (325 statements, 102 branches); B3 owns remaining constructor/diagnostic cases and independent failure corpus. Full foundation gate 361 tests/nine independent packages and existing runtime/artifact REC-01..09 passed. Twenty-nine tool contract cases include additive registry transport fixtures; schema import coverage alone is not policy evidence.
