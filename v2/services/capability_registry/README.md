# Capability Registry

- Status: BP-03.01/B1 immutable descriptor identity boundary; no HTTP hosting, durable registration, eligibility policy, deployment inventory or runtime routing yet.
- Package: `amphora-capability-registry` 0.1.0.
- Architecture: [Catalog](../../docs/Architecture/Capabilities/Catalog.md), [Tool Services](../../docs/Architecture/Capabilities/Tool_Services.md).

This owner will maintain the tool/node index. Its current [descriptor module](src/amphora_capability_registry/descriptors/README.md) binds immutable release identity, canonical metadata bytes, image/schema pins and explicit LockEntry verification. It imports only public core/tools contracts; it does not import runtime/artifact implementations, access peer tables or dispatch work. No import starts a process or network connection.

The new ReleaseDescriptor is a separate wire-v1 root containing the existing ToolDescriptor plus explicit resource/egress/checkpoint/reproducibility metadata and a restricted authority ceiling. Old ToolDescriptor, Invocation and Completion schemas and command fixtures remain unchanged. Release identity differs from deployment/replica identity; health never grants scientific eligibility or execution authority.

No authoritative registration success can be produced by this package yet. B1's immutable registration comparison is an owner domain precondition; BP-03.02 must apply it within the durable, authenticated registration transaction. BP-03.01/B2 owns structural/scientific/capacity policy objects; later children own store/routing, SDK/tools and replica acceptance.

Tests belong to `tests/descriptors/`; run `dev/run_tests.py --module registry --area descriptors --coverage`. Coverage measures all current registry source; independent builds must contain neither peer service nor scientific packages. A replacement preserves canonical release profile, exact byte comparison under existing identity, full LockEntry matching and old execution wire compatibility. Preserve durable registration history once implemented; do not substitute healthy capacity for release suitability. Synthetic numeric/sequence fixture metadata establishes no chemical or biological validity.

B1 verification: eleven owned identity cases measured 100% of the current 65-statement/six-branch denominator; semantic policy and storage are not in that implemented denominator yet. Full foundation gate 331 tests/nine independent packages and existing runtime/artifact REC-01..09 passed. Twenty-eight tool contract cases include additive registry transport fixtures; schema import coverage alone is not policy evidence.
