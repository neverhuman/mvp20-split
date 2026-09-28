# Tool Protocol Contracts

- Status: implemented initial protocol subset; `amphora-contracts-tools` 0.1.0 / wire v1
- Architecture: [Tool Services](../../docs/Architecture/Capabilities/Tool_Services.md)

## Behavior and Public Boundary

Public root exports tool bindings, input/output port declarations, descriptors, artifact-bound invocations and discriminated completions. Tool identity pins release, image digest and contract version. Invocation identity separates run/node/activation/invocation/attempt/fence. Outcomes distinguish succeeded, abstained, failed and uncertain external effect; only success carries declared output bindings. Scientific promotion is not implied by success.

## Dependencies and State

Depends only on declared core/commands contract packages and Pydantic. No runtime imports, provider calls, database access or in-process authoritative state. Scientific values and parameters are schema-bound artifacts in this initial subset. Descriptor limits bound port count and wire shape; scope/port compatibility checks belong to the accepting runtime policy, not a validator that performs I/O.

## Replacement and Verification

Preserve outcome tags, exact binding identity and failure distinctions; a retryable flag remains a proposal, not authorization to retry a physical effect. Consumers use shared valid/invalid fixtures and input/output schema bundles, including rejection of favorable outputs on an abstention and floating image names. Independent wheel installation must not pull in FastAPI, scientific kernels or the whole engine. See [verification](../../dev/README.md).

BP-02 supplies durable claims/completion/cancellation in runtime contracts. BP-03 adds registry boundaries here; deployment inventory, credential resolution and standalone tools remain later child work. This subset is not the complete future tool platform or a running scientific service. Replacements must version any additions for strict old readers and account for pinned runs.

## Owned Tests

`tests/test_wire.py` owns this package's strict input/serialization and JSON Schema conformance cases using shared language-neutral examples under `contracts/fixtures/v1`. Core additionally checks immutable scope; tools checks version/unknown-field rejection. The suite measures `src/amphora_contracts_tools`; schema import coverage alone is not semantic coverage. More schema edge cases remain future contract-change work.

From repository root: `uv run --project v2/dev --locked python v2/dev/run_tests.py --module tools --coverage`. Test and coverage reports are written under `v2/.test-results/tools/`. Preserve these tests as the package replacement boundary.

## Additive Registry Contracts (BP-03.01)

`ReleaseDescriptor` is a new wire-v1 root wrapping the unchanged ToolDescriptor with explicit finite resource bounds, CPU architecture/OS declarations, deny/allowlist egress, checkpoint compatibility, reproducibility, examples/anti-examples and a limited authority ceiling. Metadata grants no networking, deployment or scientific authority. `LockEntry` pins the whole release descriptor hash plus exact tool/image and port/checkpoint schemas; replica URLs and health never belong in a campaign lock.

`RegisterRelease` and `ReleaseRegistrationReceipt` define scoped registration payload/response shapes; the future registry command/HTTP boundary owns authentication, durable conflict handling and receipts. `EligibilityResult` keeps structural, scientific and capacity observations separate and pins the policy digest. A healthy capacity observation may coexist with scientific unreviewed/ineligible; there is no implied overall execution grant.

The registry owner defines the `amphora-tool-release-v1` canonical profile and exact byte/lock comparison. Public language-neutral metadata/canonical/lock examples are `fixtures/v1/tool_releases.json`, with transport examples in `tool_release_messages.json`. Their synthetic schema/image pins are fixture metadata, not deployed scientific tools. B2/B3 implement semantic validation and policy; .02 implements persistence, lifecycle/routing and deployment identities. No legacy descriptor/invocation/completion schema or canonical command bytes were altered by these additive roots.

B2 adds `EligibilityDecision` as a separate root wrapping the unchanged B1 observations with reason-coded policy admission, candidate/rejected selection and explicit aware observation/capacity-expiry times. Policy/resource/egress compatibility stays distinct from scientific suitability and capacity. A candidate is not an execution grant. `tool_selection_decision.json` illustrates healthy capacity with unreviewed science and a rejected selection. Registry domain objects own those decisions; DTOs do not evaluate policy or perform I/O.

## Registry Owner Operations (BP-03.02)

Additive roots describe revisioned release/deployment changes, bounded replica heartbeats, exact-lock resolution and scoped snapshots/terminal receipts. `parse_registry_command` binds nine closed registry command families to the shared canonical command envelope; registration payload scope must match authenticated identity scope. The registry handler separately authenticates actor/actions and persists authority. No transport parser grants permissions. Existing 80 schema artifacts remain unchanged; nine roots add 18 artifacts. Replay returns an original observation/receipt, including its original expiry; a new command identity is required for fresh resolution.

The V1 registry closeout adds `ReleasePage` for scoped capability/version discovery with a bounded digest cursor. This is a separate additive root (100 schema artifacts overall), not a change to execution or earlier registry records. Discovery is current inventory; lifecycle/capacity must be re-evaluated before selecting a pinned release.
