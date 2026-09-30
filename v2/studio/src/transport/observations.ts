import { decodeObservation } from "../contracts/observations.js";
import type { GraphSnapshotPage, GraphNodeDetail, GraphValuePage, GraphInvalidationPage, ReadQuery, ObservationWire } from "../contracts/observations.js";
import type { GraphScopePage, GraphTopologyPage, TopologyQuery } from "../contracts/observations.js";
import type { GraphViewCatalog, SuccessorLineage } from "../contracts/observations.js";
import type { CompletionRecord, ArtifactRef } from "../contracts/observations.js";
import { ReadFailure } from "./failure.js";
import { boundedJSON } from "./bounded_json.js";

export interface ObservationSource {
  snapshot(run: string, query: ReadQuery, cursor: string | undefined, signal: AbortSignal): Promise<GraphSnapshotPage>;
  detail(run: string, activation: string, snapshot: string, cursor: string | undefined, signal: AbortSignal): Promise<GraphNodeDetail>;
  values(run: string, activation: string, port: string, snapshot: string, cursor: string | undefined, signal: AbortSignal): Promise<GraphValuePage>;
  events(run: string, cursor: string, signal: AbortSignal): Promise<GraphInvalidationPage>;
}

export interface NavigationSource {
  scopes(run: string, snapshot: string, parent: string | undefined, cursor: string | undefined, signal: AbortSignal): Promise<GraphScopePage>;
  topology(run: string, scope: string, snapshot: string, query: TopologyQuery, cursor: string | undefined, signal: AbortSignal): Promise<GraphTopologyPage>;
}

export interface NamedViewSource {
  catalog(run: string, snapshot: string, signal: AbortSignal): Promise<GraphViewCatalog>;
  lineage(run: string, signal: AbortSignal): Promise<SuccessorLineage>;
}

export interface EvidenceSource {
  completion(run: string, completion: string, signal: AbortSignal): Promise<CompletionRecord>;
  artifact(artifact: string, signal: AbortSignal): Promise<ArtifactRef>;
  values(run: string, activation: string, port: string, snapshot: string, cursor: string | undefined, signal: AbortSignal): Promise<GraphValuePage>;
}


export class ObservationClient implements ObservationSource, NavigationSource, NamedViewSource, EvidenceSource {
  constructor(private readonly fetcher: typeof fetch = fetch, private readonly base = "/api/runtime",
    private readonly timeoutMs = 15_000, private readonly maximumBytes = 2_097_152, private readonly artifactBase = "/api/artifacts") {
    if ([base, artifactBase].some(value => !value.startsWith("/") || value.startsWith("//") || /[\\?#]/.test(value)) || timeoutMs <= 0 || maximumBytes <= 0)
      throw new Error("invalid_transport_configuration");
  }

  private async read<K extends keyof ObservationWire>(kind: K, path: string,
    params: Record<string, string | undefined>, signal: AbortSignal, namespace = "graph-observations", base = this.base): Promise<ObservationWire[K]> {
    const controller = new AbortController();
    let timedOut = false;
    const abort = () => controller.abort();
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, this.timeoutMs);
    const query = new URLSearchParams(Object.entries(params).filter((entry): entry is [string, string] => entry[1] !== undefined));
    try {
      if (controller.signal.aborted) throw new ReadFailure("aborted");
      // A native browser fetch rejects an arbitrary client object as its receiver.
      const response = await this.fetcher.call(globalThis, base + "/v1/" + namespace + "/" + path + "?" + query.toString(), {
        signal: controller.signal, credentials: "same-origin", redirect: "error", headers: { Accept: "application/json" },
      });
      if (!response.ok) await response.body?.cancel().catch(() => undefined);
      if (response.status === 401 || response.status === 403) throw new ReadFailure("denied");
      if (response.status === 404) throw new ReadFailure("unavailable");
      if (response.status === 409 || response.status === 410) throw new ReadFailure("resnapshot");
      if (!response.ok) throw new ReadFailure("network");
      const raw = await boundedJSON(response, this.maximumBytes);
      if (controller.signal.aborted) throw new ReadFailure(timedOut ? "timeout" : "aborted");
      try { return decodeObservation(kind, raw); } catch { throw new ReadFailure("invalid_response"); }
    } catch (error) {
      if (timedOut) throw new ReadFailure("timeout");
      if (signal.aborted) throw new ReadFailure("aborted");
      if (error instanceof ReadFailure) throw error;
      throw new ReadFailure("network");
    } finally {
      clearTimeout(timer);
      signal.removeEventListener("abort", abort);
    }
  }

  snapshot(run: string, query: ReadQuery, cursor: string | undefined, signal: AbortSignal) {
    return this.read("snapshot", encodeURIComponent(run) + "/nodes", { scope_key: query.scope_key ?? undefined,
      frontier_only: String(query.frontier_only ?? false), cursor, limit: "50" }, signal);
  }

  catalog(run: string, snapshot: string, signal: AbortSignal) {
    return this.read("catalog", encodeURIComponent(run) + "/views", { snapshot_token: snapshot }, signal);
  }

  lineage(run: string, signal: AbortSignal) {
    return this.read("lineage", encodeURIComponent(run) + "/lineage", {}, signal, "graph-runs");
  }

  completion(run: string, completion: string, signal: AbortSignal) {
    return this.read("completion", encodeURIComponent(run) + "/completions/" + encodeURIComponent(completion), {}, signal, "runs");
  }

  artifact(artifact: string, signal: AbortSignal) {
    return this.read("artifact", encodeURIComponent(artifact), {}, signal, "artifacts", this.artifactBase);
  }
  detail(run: string, activation: string, snapshot: string, cursor: string | undefined, signal: AbortSignal) {
    return this.read("detail", `${encodeURIComponent(run)}/nodes/${encodeURIComponent(activation)}`,
      { snapshot_token: snapshot, cursor, limit: "50" }, signal);
  }
  values(run: string, activation: string, port: string, snapshot: string, cursor: string | undefined, signal: AbortSignal) {
    return this.read("values", `${encodeURIComponent(run)}/nodes/${encodeURIComponent(activation)}/outputs/${encodeURIComponent(port)}`,
      { snapshot_token: snapshot, cursor, limit: "50" }, signal);
  }
  events(run: string, cursor: string, signal: AbortSignal) {
    return this.read("events", encodeURIComponent(run) + "/invalidations", { cursor, limit: "100" }, signal);
  }
  scopes(run: string, snapshot: string, parent: string | undefined, cursor: string | undefined, signal: AbortSignal) {
    return this.read("scopes", `${encodeURIComponent(run)}/scopes`,
      { snapshot_token: snapshot, parent_activation_id: parent, cursor, limit: "50" }, signal);
  }
  topology(run: string, scope: string, snapshot: string, query: TopologyQuery, cursor: string | undefined, signal: AbortSignal) {
    return this.read("topology", `${encodeURIComponent(run)}/scopes/${encodeURIComponent(scope)}/topology`,
      { snapshot_token: snapshot, focus_activation_id: query.focus_activation_id ?? undefined,
        radius: String(query.radius ?? 1), cursor, limit: "50" }, signal);
  }
}
