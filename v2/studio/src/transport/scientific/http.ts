import { boundedJSON } from "../bounded_json.js";
import { ScientificReadFailure } from "./failure.js";

export class ScientificHTTP {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly timeoutMs = 15_000) {
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1) throw new Error("invalid_transport_configuration");
  }

  async post<T>(path: string, query: object, decode: (value: unknown) => T, signal: AbortSignal): Promise<T> {
    // Only reviewed same-origin owner routes can be used, including by future callers of this helper.
    if (!/^\/api\/(knowledge\/v1\/graph-explore\/(catalog|entities|neighborhood|object)|research\/v1\/research-explore\/(catalog|specimens|properties|observation-series))$/.test(path))
      throw new ScientificReadFailure("invalid_request");
    let body: string;
    try { body = JSON.stringify(query); } catch { throw new ScientificReadFailure("invalid_request"); }
    if (new TextEncoder().encode(body).byteLength > 262144) throw new ScientificReadFailure("limit");
    const controller = new AbortController();
    let timedOut = false;
    const abort = () => controller.abort();
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    try {
      if (controller.signal.aborted) throw new ScientificReadFailure("aborted");
      const response = await this.fetcher.call(globalThis, path, { method: "POST", body, signal: controller.signal,
        credentials: "same-origin", redirect: "error", headers: { Accept: "application/json", "Content-Type": "application/json" } });
      if (!response.ok) {
        await response.body?.cancel().catch(() => undefined);
        throw new ScientificReadFailure(response.status === 401 || response.status === 403 ? "denied" :
          response.status === 404 ? "unavailable" : response.status === 409 || response.status === 410 ? "query_conflict" :
          response.status === 413 ? "limit" : response.status === 422 ? "invalid_request" : "network");
      }
      let result: T;
      try { result = decode(await boundedJSON(response, 1048576)); }
      catch { throw new ScientificReadFailure("invalid_response"); }
      if (controller.signal.aborted) throw new ScientificReadFailure(timedOut ? "timeout" : "aborted");
      return result;
    } catch (error) {
      if (timedOut) throw new ScientificReadFailure("timeout");
      if (signal.aborted) throw new ScientificReadFailure("aborted");
      if (error instanceof ScientificReadFailure) throw error;
      throw new ScientificReadFailure("network");
    } finally {
      clearTimeout(timer);
      signal.removeEventListener("abort", abort);
    }
  }
}
