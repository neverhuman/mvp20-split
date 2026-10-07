import type { ArtifactRef, GraphNodeDetail, GraphSnapshotPage, GraphValuePage } from "../../contracts/observations.js";
import { ReadFailure } from "../../transport/failure.js";
import { artifactKey, EvidenceContext } from "../evidence_context.js";
import { immutable } from "../explore/context.js";

/** Proves a point's subject occurs in explicitly loaded, pinned Runtime outputs. */
export class QualityAttachment {
  readonly cut: GraphSnapshotPage["snapshot"]["cut"];
  readonly activationId: string;
  readonly nodeLabel: string;
  readonly operationalState: GraphNodeDetail["node"]["status"];
  readonly port: string;
  readonly complete: boolean;
  private readonly artifacts: readonly ArtifactRef[];
  constructor(anchor: GraphSnapshotPage["snapshot"], detail: GraphNodeDetail, port: string, pages: readonly GraphValuePage[]) {
    if (pages.length < 1 || pages.length > 32) throw new ReadFailure("invalid_response");
    const context = new EvidenceContext(anchor, detail);
    const artifacts: ArtifactRef[] = [];
    let loaded = 0;
    for (const [index, page] of pages.entries()) {
      if (index > 0 && pages[index - 1]!.next_cursor === null) throw new ReadFailure("invalid_response");
      context.values(port, page, loaded);
      loaded += page.items.length;
      for (const item of page.items) if (item.value.kind === "artifact") artifacts.push(item.value.artifact);
    }
    this.cut = immutable(anchor.cut); this.activationId = detail.node.activation_id;
    this.nodeLabel = detail.node.path.node_id;
    this.operationalState = detail.node.status; this.port = port;
    this.complete = pages[pages.length - 1]!.next_cursor === null;
    this.artifacts = immutable(artifacts); Object.freeze(this);
  }
  contains(subject: ArtifactRef) { return this.artifacts.some(ref => artifactKey(ref) === artifactKey(subject)); }
}
