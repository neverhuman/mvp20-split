import { ScientificReadFailure } from "./failure.js";

export function canonical(value: unknown): string {
  if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number" && Number.isSafeInteger(value)) return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") return "{" + Object.keys(value).sort().map(key => JSON.stringify(key) + ":" + canonical((value as Record<string, unknown>)[key])).join(",") + "}";
  throw new ScientificReadFailure("invalid_request");
}

export function same(left: unknown, right: unknown): boolean { return canonical(left) === canonical(right); }
export function requireReply(condition: boolean): asserts condition { if (!condition) throw new ScientificReadFailure("invalid_response"); }

export function normalized<T extends object>(request: T, defaults: Record<string, unknown>, decode: (value: unknown) => T): T {
  try {
    const copy = structuredClone(request) as Record<string, unknown>;
    for (const [key, value] of Object.entries(defaults)) if (copy[key] === undefined) copy[key] = value;
    return decode(copy);
  } catch { throw new ScientificReadFailure("invalid_request"); }
}

export async function fingerprint(format: string, view: string, query: object): Promise<string> {
  const request = { ...query } as Record<string, unknown>;
  delete request.position;
  const bytes = new TextEncoder().encode(canonical({ format, view, request }));
  let digest: ArrayBuffer;
  try { digest = await crypto.subtle.digest("SHA-256", bytes); }
  catch { throw new ScientificReadFailure("invalid_response"); }
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, "0")).join("");
}

export function checkPage(page: { request: object; query_sha256: string; next_position: { query_sha256: string } | null }, request: object, digest: string) {
  requireReply(same(page.request, request) && page.query_sha256 === digest);
  requireReply(page.next_position === null || page.next_position.query_sha256 === digest);
}

export async function queryDigest(format: string, view: string, query: { position?: { query_sha256: string } | null }): Promise<string> {
  const digest = await fingerprint(format, view, query);
  if (query.position && query.position.query_sha256 !== digest) throw new ScientificReadFailure("query_conflict");
  return digest;
}

export function checkWindow(start: number, returned: number, limit: number, total: number, next: number | null) {
  requireReply(returned === Math.min(limit, total - start) && start <= total);
  requireReply(next === (start + returned === total ? null : start + returned));
}
