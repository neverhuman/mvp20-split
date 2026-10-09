import { decodeLaunch } from "../../contracts/launch.js";
import type { LaunchWire } from "../../contracts/launch.js";
import { boundedJSON } from "../bounded_json.js";
import type { LaunchSubmission } from "./submission.js";

export class LaunchFailure extends Error {
  constructor(readonly kind: "denied" | "missing" | "busy" | "conflict" | "invalid_request" | "unavailable" | "invalid_response") { super(kind); }
}
/** Same-origin, cookie-only adapter. No Runtime admission is posted from this client. */
export class LaunchClient {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly timeoutMs = 15_000) {}
  private async read<K extends "catalog" | "receipt">(kind: K, path: string, signal: AbortSignal, command?: LaunchSubmission): Promise<LaunchWire[K]> {
    const controller = new AbortController(), abort = () => controller.abort();
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(abort, this.timeoutMs);
    try {
      if (controller.signal.aborted) throw new LaunchFailure("unavailable");
      const response = await this.fetcher.call(globalThis, "/api/deployment/v1/" + path, {
        method: command ? "POST" : "GET", ...(command ? { body: command.body } : {}),
        credentials: "same-origin", redirect: "error", signal: controller.signal,
        headers: { Accept: "application/json", ...(command ? { "Content-Type": "application/json" } : {}) },
      });
      if (response.status === 401 || response.status === 403) { await response.body?.cancel(); throw new LaunchFailure("denied"); }
      if (response.status === 404) { await response.body?.cancel(); throw new LaunchFailure("missing"); }
      if (!response.ok) {
        const value = await boundedJSON(response, 4096) as { reason_code?: unknown };
        if (response.status === 409 && value.reason_code === "launch_request_conflict") throw new LaunchFailure("conflict");
        if (response.status === 409 && value.reason_code === "launch_slot_busy") throw new LaunchFailure("busy");
        if (response.status === 422) throw new LaunchFailure("invalid_request");
        throw new LaunchFailure("unavailable");
      }
      const raw = await boundedJSON(response, 1_048_576);
      if (controller.signal.aborted) throw new LaunchFailure("unavailable");
      try { return decodeLaunch(kind, raw); } catch { throw new LaunchFailure("invalid_response"); }
    } catch (error) { throw error instanceof LaunchFailure ? error : new LaunchFailure("unavailable"); }
    finally { clearTimeout(timer); signal.removeEventListener("abort", abort); }
  }
  profiles(signal: AbortSignal) { return this.read("catalog", "campaign-launch-profiles", signal); }
  submit(command: LaunchSubmission, signal: AbortSignal) { return this.read("receipt", "campaign-launches", signal, command); }
  receipt(command: LaunchSubmission, signal: AbortSignal) {
    return this.read("receipt", "campaign-launches/" + encodeURIComponent(command.request.identity.command_id), signal);
  }
}
