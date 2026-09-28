# Tool Protocol Contracts

- Status: implemented initial protocol subset; `amphora-contracts-tools` 0.1.0 / wire v1
- Architecture: [Tool Services](../../docs/Architecture/Capabilities/Tool_Services.md)

## Behavior and Public Boundary

Public root exports tool bindings, input/output port declarations, descriptors, artifact-bound invocations and discriminated completions. Tool identity pins release, image digest and contract version. Invocation identity separates run/node/activation/invocation/attempt/fence. Outcomes distinguish succeeded, abstained, failed and uncertain external effect; only success carries declared output bindings. Scientific promotion is not implied by success.

## Dependencies and State

Depends only on the declared core contract package and Pydantic. No runtime imports, provider calls, database access or in-process authoritative state. Scientific values and parameters are schema-bound artifacts in this initial subset. Descriptor limits bound port count and wire shape; scope/port compatibility checks belong to the accepting runtime policy, not a validator that performs I/O.

## Replacement and Verification

Preserve outcome tags, exact binding identity and failure distinctions; a retryable flag remains a proposal, not authorization to retry a physical effect. Consumers use shared valid/invalid fixtures and input/output schema bundles, including rejection of favorable outputs on an abstention and floating image names. Independent wheel installation must not pull in FastAPI, scientific kernels or the whole engine. See [verification](../../dev/README.md).

Descriptor lifecycle, deployment inventory, resource profiles, credential resolution, durable claims and cancellation/heartbeat APIs remain BP-02/03 work. This subset is not the complete future tool descriptor or a running tool service. Replacements must version any additions for strict old readers and account for future pinned runs.

## Owned Tests

`tests/test_wire.py` owns this package's strict input/serialization and JSON Schema conformance cases using shared language-neutral examples under `contracts/fixtures/v1`. Core additionally checks immutable scope; tools checks version/unknown-field rejection. The suite measures `src/amphora_contracts_tools`; schema import coverage alone is not semantic coverage. More schema edge cases remain future contract-change work.

From repository root: `uv run --project v2/dev --locked python v2/dev/run_tests.py --module tools --coverage`. Test and coverage reports are written under `v2/.test-results/tools/`. Preserve these tests as the package replacement boundary.
