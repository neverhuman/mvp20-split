import { boundedJSON } from "../bounded_json.js";
import { ScientificReadFailure } from "./failure.js";
import { allowedRoute } from "./routes.js";
import { boundedBytes } from "./bytes.js";

export class ScientificHTTP {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly timeoutMs = 15_000) {
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1) throw new Error("invalid_transport_configuration");
  }

  async post<T>(path: string, query: object, decode: (value: unknown) => T, signal: AbortSignal): Promise<T> {
    let body: string;
    try { body = JSON.stringify(query); } catch { throw new ScientificReadFailure("invalid_request"); }
    if (new TextEncoder().encode(body).byteLength > 262144) throw new ScientificReadFailure("limit");
    return this.request("POST", path, body, response => this.json(response, decode), signal);
  }

  get<T>(path: string, decode: (value: unknown) => T, signal: AbortSignal): Promise<T> {
    return this.request("GET", path, undefined, response => this.json(response, decode), signal);
  }

  content(path: string, size: number, media: string, signal: AbortSignal) {
    if (!Number.isSafeInteger(size) || size < 0 || size > 4194304 || !path.endsWith("/content")) throw new ScientificReadFailure("limit");
    return this.request("GET", path, undefined, response => boundedBytes(response, size, media), signal);
  }

  private async json<T>(response: Response, decode: (value: unknown) => T): Promise<T> {
    try { return decode(await boundedJSON(response, 1048576)); }
    catch { throw new ScientificReadFailure("invalid_response"); }
  }

  private async request<T>(method: "GET" | "POST", path: string, body: string | undefined, read: (response: Response) => Promise<T>, signal: AbortSignal): Promise<T> {
    if (!allowedRoute(method, path)) throw new ScientificReadFailure("invalid_request");
    const controller = new AbortController();
    let timedOut = false;
    const abort = () => controller.abort();
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    try {
      if (controller.signal.aborted) throw new ScientificReadFailure("aborted");
      const response = await this.fetcher.call(globalThis, path, { method, ...(body === undefined ? {} : { body }), signal: controller.signal,
        credentials: "same-origin", redirect: "error", headers: body === undefined ? { Accept: "*/*" } : { Accept: "application/json", "Content-Type": "application/json" } });
      if (!response.ok) {
        await response.body?.cancel().catch(() => undefined);
        throw new ScientificReadFailure(response.status === 401 || response.status === 403 ? "denied" :
          response.status === 404 ? "unavailable" : response.status === 409 || response.status === 410 ? "query_conflict" :
          response.status === 413 ? "limit" : response.status === 422 ? "invalid_request" : "network");
      }
      const result = await read(response);
      if (controller.signal.aborted) throw new ScientificReadFailure(timedOut ? "timeout" : "aborted");
      return result;
    } catch (error) {
      if (timedOut) throw new ScientificReadFailure("timeout");
      if (signal.aborted) throw new ScientificReadFailure("aborted");
      if (error instanceof ScientificReadFailure) throw error;
      throw new ScientificReadFailure("network");
    } finally {
      controller.abort();
      clearTimeout(timer);
      signal.removeEventListener("abort", abort);
    }
  }
}
