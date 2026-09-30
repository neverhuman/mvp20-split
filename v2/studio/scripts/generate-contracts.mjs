/** Reproducible consumer types and schema bytes; Python publications remain authoritative. */
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";
import { compile } from "json-schema-to-typescript";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(root, "../contracts/schemas/v1");
const target = resolve(root, "src/contracts/generated");
const roots = {
  snapshot: ["graph-runtime.snapshot-page", "GraphSnapshotPage"],
  detail: ["graph-runtime.node-detail", "GraphNodeDetail"],
  values: ["graph-runtime.value-page", "GraphValuePage"],
  events: ["graph-runtime.invalidation-page", "GraphInvalidationPage"],
  scopes: ["graph-runtime.scope-page", "GraphScopePage"],
  topology: ["graph-runtime.topology-page", "GraphTopologyPage"],
  catalog: ["graph-runtime.view-catalog", "GraphViewCatalog"],
  lineage: ["graph-runtime.successor-lineage", "SuccessorLineage"],
};
const check = process.argv.includes("--check");
const manifest = {};
const schemas = {};
await mkdir(target, { recursive: true });

async function output(name, body) {
  const path = resolve(target, name);
  if (check) {
    const old = await readFile(path, "utf8").catch(() => "");
    if (old !== body) throw new Error(`Generated contract drift: ${name}; run npm run generate`);
  } else {
    await writeFile(path, body, "utf8");
  }
}

for (const [key, [file, title]] of Object.entries(roots)) {
  const bytes = await readFile(resolve(source, `${file}.serialization.json`));
  const schema = JSON.parse(bytes);
  schemas[key] = schema;
  manifest[key] = { source: `contracts/schemas/v1/${file}.serialization.json`, sha256: createHash("sha256").update(bytes).digest("hex") };
  const declarations = await compile(schema, title, {
    bannerComment: "/* Generated from the published Python-owned serialization schema. Do not edit. */",
    additionalProperties: false, ignoreMinAndMaxItems: true, unknownAny: true,
  });
  await output(`${key}.d.ts`, declarations);
}
await output("schemas.json", JSON.stringify(schemas, null, 2) + "\n");
await output("manifest.json", JSON.stringify(manifest, null, 2) + "\n");
console.log(`Studio contracts ${check ? "verified" : "generated"}: ${Object.keys(roots).length} published roots`);
