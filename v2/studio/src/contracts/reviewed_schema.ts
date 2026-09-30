import { decodeAuthoring } from "./authoring.js";
import type { DefinitionSchema, DefinitionUniverse } from "./authoring.js";

/** Exact-byte verification only. Schema form support and execution eligibility are separate. */
export async function reviewedSchema(raw: unknown, universe: DefinitionUniverse,
  reference: DefinitionSchema["reference"]): Promise<Readonly<Record<string, unknown>>> {
  const value = decodeAuthoring("schema", raw);
  const sameReference = (candidate: DefinitionSchema["reference"]) =>
    candidate.schema_id === reference.schema_id && candidate.version === reference.version && candidate.sha256 === reference.sha256;
  if (value.scope.tenant_id !== universe.scope.tenant_id || value.scope.project_id !== universe.scope.project_id ||
      value.universe_sha256 !== universe.universe_sha256 || !sameReference(value.reference) || !universe.schemas.some(sameReference))
    throw new Error("schema_identity_mismatch");
  let binary: string;
  try { binary = atob(value.schema_bytes_base64); }
  catch { throw new Error("invalid_schema_encoding"); }
  if (binary.length > 65_536 || btoa(binary) !== value.schema_bytes_base64) throw new Error("invalid_schema_encoding");
  const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), byte => byte.toString(16).padStart(2, "0")).join("");
  if (digest !== reference.sha256) throw new Error("schema_digest_mismatch");
  let parsed: unknown;
  try { parsed = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
  catch { throw new Error("invalid_schema_document"); }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("invalid_schema_document");
  return parsed as Readonly<Record<string, unknown>>;
}
