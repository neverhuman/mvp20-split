import type { DefinitionUniverse, ReleaseSnapshot } from "../../src/contracts/authoring.js";
import { scope } from "./authoring.js";

export function registryFixture() {
  const schema = { schema_id: "numeric-input", version: "1" as const, sha256: "a".repeat(64) };
  const binding = { capability_id: "synthetic.numeric", release: "1.0.0", contract_version: "1" as const, image_sha256: "b".repeat(64) };
  const release: ReleaseSnapshot = { scope, revision: 1, status: "active", lock: {
    tool: binding, descriptor_sha256: "c".repeat(64), checkpoint_schema: null,
    input_schemas: [{ port: "parameters", schema_ref: schema }], output_schemas: [],
  }, descriptor: { schema_version: "1", tool: { schema_version: "1", binding, purpose: "Synthetic example",
    applicability: ["synthetic-tests"], side_effects: "pure", inputs: [{ name: "parameters", representation: "numeric-vector", unit: "1", required: true, schema_ref: schema }], outputs: [], checkpoint_schema: null },
    resources: { architectures: ["x86_64"], operating_systems: ["linux"], cpu_millicores: 1000, memory_mib: 128, gpu_count: 0, timeout_seconds: 60, max_batch_size: 1, max_parallel_invocations: 1 },
    egress: { mode: "deny" }, checkpoint: { mode: "none", readable_schema_sha256: [] }, authority_ceiling: "synthetic_only", reproducibility: "deterministic", examples: ["Synthetic"], anti_examples: ["No scientific validity"] } };
  const universe: DefinitionUniverse = { scope, universe_sha256: "d".repeat(64), reviewed_tools: [structuredClone(release.lock)], schemas: [schema] };
  return { release, universe };
}

