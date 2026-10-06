import { decodeSupervision } from "../../contracts/supervision.js";
import type { InspectionSnapshot, SupervisionWire } from "../../contracts/supervision.js";
import { boundedJSON } from "../bounded_json.js";
import { ReadFailure } from "../failure.js";
export interface InspectionBinding { run: string; scope: { tenant_id: string; project_id: string } }
export interface SupervisionSource {
  checkpoints(binding: InspectionBinding, cursor: string | null, signal: AbortSignal): Promise<SupervisionWire["checkpoints"]>;
  requests(binding: InspectionBinding, decision: string, snapshot: InspectionSnapshot, cursor: string | null, signal: AbortSignal): Promise<SupervisionWire["requests"]>;
  context(binding: InspectionBinding, decision: string, request: string, snapshot: InspectionSnapshot, cursor: string | null, signal: AbortSignal): Promise<SupervisionWire["context"]>;
  responses(binding: InspectionBinding, decision: string, request: string, snapshot: InspectionSnapshot, cursor: string | null, signal: AbortSignal): Promise<SupervisionWire["responses"]>;
  decision(binding: InspectionBinding, decision: string, signal: AbortSignal): Promise<SupervisionWire["decision"]>;
}
export class SupervisionClient implements SupervisionSource {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly timeoutMs = 15000) {
    if (!Number.isSafeInteger(timeoutMs) || timeoutMs < 1) throw new Error("invalid_transport_configuration");
  }
  private async read<K extends keyof SupervisionWire>(kind: K, binding: InspectionBinding, decision: string | null,
    request: string | null, snapshot: InspectionSnapshot | null, cursor: string | null, signal: AbortSignal): Promise<SupervisionWire[K]> {
    const part = (value: string) => { if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(value)) throw new ReadFailure("invalid_response"); return encodeURIComponent(value); };
    let path = `/api/runtime/v1/supervision/runs/${part(binding.run)}/checkpoints`;
    if (decision) path += `/${part(decision)}/requests`;
    if (request) path += `/${part(request)}/${kind}`;
    if (kind === "decision") path = `/api/runtime/v1/supervision/decisions/${part(binding.run)}/${part(decision!)}`;
    const query = new URLSearchParams(kind === "decision" ? {} : { limit: "10" });
    if (snapshot) query.set("snapshot_token", snapshot.snapshot_token);
    if (cursor) query.set("cursor", cursor);
    const controller = new AbortController(); let timedOut = false;
    const abort = () => controller.abort(); signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    try {
      if (controller.signal.aborted) throw new ReadFailure("aborted");
      const response = await this.fetcher.call(globalThis, path + "?" + query, {
        signal: controller.signal, credentials: "same-origin", redirect: "error", headers: { Accept: "application/json" },
      });
      if (!response.ok) { await response.body?.cancel().catch(() => undefined);
        throw new ReadFailure(response.status === 401 || response.status === 403 ? "denied" : response.status === 404 ? "unavailable" :
          response.status === 409 || response.status === 410 ? "resnapshot" : "network"); }
      let value: SupervisionWire[K];
      try { value = decodeSupervision(kind, await boundedJSON(response, 262144)); } catch { throw new ReadFailure("invalid_response"); }
      if (controller.signal.aborted) throw new ReadFailure("aborted");
      const ref = "snapshot" in value ? value.snapshot.cut : value.reference;
      if (ref.run_id !== binding.run || ref.scope.tenant_id !== binding.scope.tenant_id || ref.scope.project_id !== binding.scope.project_id)
        throw new ReadFailure("invalid_response");
      const checkScopes = (node: unknown): void => {
        if (!node || typeof node !== "object") return;
        const record = node as Record<string, unknown>;
        if ("tenant_id" in record && (record.tenant_id !== binding.scope.tenant_id || record.project_id !== binding.scope.project_id)) throw new ReadFailure("invalid_response");
        if ("run_id" in record && record.run_id !== binding.run) throw new ReadFailure("invalid_response");
        for (const child of Object.values(record)) checkScopes(child);
      };
      checkScopes(value);
      if ("reference" in value && value.reference.decision_id !== decision) throw new ReadFailure("invalid_response");
      if ("request_sha256" in value && value.request_sha256 !== request) throw new ReadFailure("invalid_response");
      if (snapshot && "snapshot" in value && (value.snapshot.epoch !== snapshot.epoch || value.snapshot.cut.revision !== snapshot.cut.revision || value.snapshot.cut.frontier_revision !== snapshot.cut.frontier_revision || value.snapshot.cut.plan_sha256 !== snapshot.cut.plan_sha256))
        throw new ReadFailure("resnapshot");
      return value;
    } catch (error) {
      if (timedOut) throw new ReadFailure("timeout");
      if (signal.aborted) throw new ReadFailure("aborted");
      throw error instanceof ReadFailure ? error : new ReadFailure("network");
    } finally { clearTimeout(timer); signal.removeEventListener("abort", abort); controller.abort(); }
  }
  checkpoints(b: InspectionBinding, c: string | null, s: AbortSignal) { return this.read("checkpoints", b, null, null, null, c, s); }
  requests(b: InspectionBinding, d: string, w: InspectionSnapshot, c: string | null, s: AbortSignal) { return this.read("requests", b, d, null, w, c, s); }
  context(b: InspectionBinding, d: string, r: string, w: InspectionSnapshot, c: string | null, s: AbortSignal) { return this.read("context", b, d, r, w, c, s); }
  responses(b: InspectionBinding, d: string, r: string, w: InspectionSnapshot, c: string | null, s: AbortSignal) { return this.read("responses", b, d, r, w, c, s); }
  decision(b: InspectionBinding, d: string, s: AbortSignal) { return this.read("decision", b, d, null, null, null, s); }
}
