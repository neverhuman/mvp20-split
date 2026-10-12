/** Bounded numeric wire encoding; canonical owner hashes are not reproduced here. */
export function checkJSON(value: unknown, numeric: boolean, depth = 0): void {
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number" && (numeric ? Number.isFinite(value) : Number.isSafeInteger(value))) return;
  if (typeof value === "string" && !/[\uD800-\uDFFF]/u.test(value)) return;
  if (depth >= 64 || typeof value !== "object" || value === null) throw new Error("invalid_command_value");
  if (Array.isArray(value)) { for (const item of value) checkJSON(item, numeric, depth + 1); return; }
  if (Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null) throw new Error("invalid_command_value");
  for (const [key, item] of Object.entries(value)) { checkJSON(key, numeric); checkJSON(item, numeric, depth + 1); }
}

/** Wire encoding only; owner DTO normalization/canonical hashing still happens server-side. */
export function numericJSON(value: unknown): string {
  if (typeof value === "number") return Number.isInteger(value) && !Number.isSafeInteger(value) ? value.toExponential() : JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(numericJSON).join(",") + "]";
  if (value && typeof value === "object") return "{" + Object.entries(value).map(([key, item]) => JSON.stringify(key) + ":" + numericJSON(item)).join(",") + "}";
  return JSON.stringify(value);
}
