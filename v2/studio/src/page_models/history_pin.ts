import type { ArtifactRef, CompletionRecord, GraphNode, GraphNodeDetail, GraphTopologyPage, GraphValuePage, ReadCut, SuccessorLineage } from "../contracts/observations.js";
import type { MonitorView } from "./monitor.js";
import type { NavigationView } from "./navigation.js";
import type { EvidenceView } from "./evidence.js";
import type { NamedViewsState } from "./named_views.js";
import { cutKey, requireContext } from "./graph_window.js";
import { EvidenceContext, artifactKey } from "./evidence_context.js";
import type { Viewport } from "./scene.js";

export interface InspectionSelection {
  readonly monitor: MonitorView;
  readonly navigation?: NavigationView;
  readonly evidence?: EvidenceView;
  readonly namedViews?: NamedViewsState;
}
export interface InspectionPin {
  readonly id: string;
  readonly capturedAt: string;
  readonly cut: ReadCut;
  readonly source: "occurrence_topology" | "activation_inventory";
  readonly nodes: readonly GraphNode[];
  readonly edges: readonly GraphTopologyPage["edges"][number][];
  readonly totalNodes: number;
  readonly scopeKey: string | null;
  readonly selection: string | null;
  readonly detail: GraphNodeDetail | null;
  readonly completion: CompletionRecord | null;
  readonly values: GraphValuePage | null;
  readonly artifact: ArtifactRef | null;
  readonly lineage: SuccessorLineage | null;
  readonly viewport: Viewport;
}
function immutable<T>(value: T): T {
  if (value && typeof value === "object") { for (const child of Object.values(value)) immutable(child); Object.freeze(value); }
  return value;
}

/** Retain verified finite observations only; there is deliberately no historical fetch capability. */
export function captureInspection(id: string, capturedAt: string, selection: InspectionSelection): InspectionPin {
  const monitor = selection.monitor, window = monitor.window;
  if (!window || !["ready", "empty"].includes(monitor.phase)) throw new Error("inspection_not_current");
  const cut = window.snapshot.cut, nav = selection.navigation;
  const topology = nav?.topologyPhase === "ready" && nav.topology && cutKey(nav.topology.page.cut) === cutKey(cut) ? nav.topology : null;
  const offset = topology && nav && nav.offset < topology.page.nodes.length ? nav.offset : 0;
  const nodes = topology ? topology.page.nodes.slice(offset, offset + 200).map(node => node.activation) : window.nodes.slice(0, 200);
  const ids = new Set(nodes.map(node => node.activation_id));
  const detail = monitor.detailPhase === "ready" ? monitor.detail : null;
  if (detail && detail.node.activation_id !== monitor.selection) throw new Error("selection_mismatch");
  const context = detail ? new EvidenceContext(window.snapshot, detail) : null;
  const evidence = selection.evidence;
  const completion = context && evidence?.completion.phase === "ready" && evidence.completion.value
    ? context.completion(evidence.completion.value.result.attempt_id, evidence.completion.value) : null;
  const valuePage = evidence?.values.phase === "ready" ? evidence.values.value : null;
  const values = context && valuePage ? context.values(valuePage.port, valuePage, valuePage.items[0]?.index ?? 0) : null;
  let artifact: ArtifactRef | null = null;
  if (context && evidence?.artifact.phase === "ready" && evidence.artifact.value) {
    const actual = evidence.artifact.value;
    const refs = (detail?.outputs ?? []).flatMap(output => output.artifact ? [output.artifact] : []);
    if (completion?.result.outcome.status === "succeeded") {
      refs.push(...completion.result.outcome.outputs.map(output => output.artifact));
      if (completion.result.outcome.checkpoint) refs.push(completion.result.outcome.checkpoint);
    }
    for (const item of values?.items ?? []) if (item.value.kind === "artifact") refs.push(item.value.artifact);
    const expected = refs.find(ref => artifactKey(ref) === artifactKey(actual));
    if (!expected) throw new Error("unlinked_artifact");
    artifact = context.artifact(expected, actual);
  }
  const lineage = selection.namedViews?.lineagePhase === "ready" ? selection.namedViews.lineage : null;
  if (lineage) {
    requireContext({ scope: cut.scope, run: cut.run_id }, lineage.scope, lineage.run_id);
    if (lineage.plan_sha256 !== cut.plan_sha256) throw new Error("lineage_plan_mismatch");
  }
  const pin: InspectionPin = { id, capturedAt, cut, source: topology ? "occurrence_topology" : "activation_inventory", nodes,
    edges: topology?.visibleEdges.filter(edge => ids.has(edge.source) && ids.has(edge.target)) ?? [],
    totalNodes: topology?.page.node_count ?? window.snapshot.node_count, scopeKey: topology?.page.graph_scope.scope_key ?? null,
    selection: monitor.selection, detail, completion, values, artifact, lineage,
    viewport: nav?.viewport ?? { x: 24, y: 24, zoom: 0.85 } };
  if (new TextEncoder().encode(JSON.stringify(pin)).length > 2_097_152) throw new Error("inspection_pin_size_exceeded");
  return immutable(structuredClone(pin));
}
