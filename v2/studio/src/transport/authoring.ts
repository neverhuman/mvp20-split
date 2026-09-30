import { decodeAuthoring } from "../contracts/authoring.js";
import type { AuthoringWire, DefinitionSchema } from "../contracts/authoring.js";
import { boundedJSON } from "./bounded_json.js";
import { Submission } from "./submission.js";

export type AuthoringFailureKind = "aborted" | "timeout" | "denied" | "unavailable" | "stale" | "invalid_response" | "network";
export class AuthoringFailure extends Error {
  constructor(readonly kind: AuthoringFailureKind, readonly commandUnresolved: boolean) { super("authoring_" + kind); }
}

/** Public same-origin adapters authenticate/reroute server-side; this client carries no owner key. */
export class AuthoringClient {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly runtimeBase = "/api/runtime",
    private readonly registryBase = "/api/registry", private readonly timeoutMs = 15_000, private readonly maximumBytes = 2_097_152) {
    if ([runtimeBase, registryBase].some(value => !value.startsWith("/") || value.startsWith("//") || /[\\?#]/.test(value)) ||
      !Number.isFinite(timeoutMs) || timeoutMs <= 0 || !Number.isSafeInteger(maximumBytes) || maximumBytes <= 0)
      throw new Error("invalid_transport_configuration");
  }

  private async request<K extends keyof AuthoringWire>(kind: K, path: string, signal: AbortSignal,
    params: Record<string, string | undefined> = {}, submission?: Submission, base = this.runtimeBase): Promise<AuthoringWire[K]> {
    const controller = new AbortController();
    const abort = () => controller.abort();
    let timedOut = false, dispatched = false;
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    const failure = (kind: AuthoringFailureKind) => new AuthoringFailure(kind, !!submission && dispatched);
    const query = new URLSearchParams(Object.entries(params).filter((entry): entry is [string, string] => entry[1] !== undefined));
    try {
      if (controller.signal.aborted) throw failure("aborted");
      dispatched = true;
      const response = await this.fetcher.call(globalThis, base + "/v1/" + path + (query.size ? "?" + query.toString() : ""), {
        method: submission ? "POST" : "GET", ...(submission ? { body: submission.body } : {}),
        signal: controller.signal, credentials: "same-origin", redirect: "error",
        headers: submission ? { Accept: "application/json", "Content-Type": "application/json" } : { Accept: "application/json" },
      });
      if (!response.ok) await response.body?.cancel().catch(() => undefined);
      if (response.status === 401 || response.status === 403) throw failure("denied");
      if (response.status === 404) throw failure("unavailable");
      if (response.status === 409 || response.status === 410) throw failure("stale");
      if (!response.ok) throw failure("network");
      let value: AuthoringWire[K];
      try { value = decodeAuthoring(kind, await boundedJSON(response, this.maximumBytes)); }
      catch { throw failure("invalid_response"); }
      if (controller.signal.aborted) throw failure(timedOut ? "timeout" : "aborted");
      return value;
    } catch (error) {
      if (timedOut) throw failure("timeout");
      if (signal.aborted) throw failure("aborted");
      if (error instanceof AuthoringFailure) throw error;
      throw failure("network");
    } finally { clearTimeout(timer); signal.removeEventListener("abort", abort); }
  }

  async submit(command: Submission, signal: AbortSignal) {
    const receipt = await this.request(command.receiptKind, command.path, signal, {}, command);
    try { command.verify(receipt); } catch { throw new AuthoringFailure("invalid_response", true); }
    return receipt;
  }

  async receipt(command: Submission, signal: AbortSignal) {
    try {
      const receipt = await this.request(command.receiptKind, command.receiptPath, signal);
      try { command.verify(receipt); } catch { throw new AuthoringFailure("invalid_response", true); }
      return receipt;
    } catch (error) {
      // A failed read cannot establish the outcome of the original submission, including a 404.
      throw new AuthoringFailure(error instanceof AuthoringFailure ? error.kind : "network", true);
    }
  }

  drafts(after: string | undefined, signal: AbortSignal) { return this.request("page", "definition-drafts", signal, { limit: "50", after }); }
  draft(id: string, revision: number | undefined, signal: AbortSignal) {
    return this.request("draft", "definition-drafts/" + encodeURIComponent(id), signal, { revision: revision?.toString() });
  }
  validation(id: string, signal: AbortSignal) { return this.request("validation", "definition-validations/" + encodeURIComponent(id), signal); }
  universe(signal: AbortSignal) { return this.request("universe", "definition-universe", signal); }
  schema(reference: DefinitionSchema["reference"], universe: string, signal: AbortSignal) {
    return this.request("schema", "definition-schemas/" + encodeURIComponent(reference.sha256), signal,
      { schema_id: reference.schema_id, version: reference.version, universe_sha256: universe });
  }
  releases(after: string | undefined, signal: AbortSignal) {
    return this.request("releases", "releases", signal, { limit: "50", after }, undefined, this.registryBase);
  }
  release(digest: string, signal: AbortSignal) {
    return this.request("release", "releases/" + encodeURIComponent(digest), signal, {}, undefined, this.registryBase);
  }
}
