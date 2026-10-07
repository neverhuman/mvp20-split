import type { QualityProjection } from "../../page_models/quality/projection.js";
import type { QualityAttachment } from "../../page_models/quality/attachment.js";
import { GraphCanvas } from "../graph_canvas.js";

export function QualityExecutionGraph({ projection, inspect }: { projection: QualityProjection; inspect?: (attachment: QualityAttachment) => void }) {
  const attachment = projection.attachment;
  if (!attachment) return null;
  return <div className="quality-linked-graph"><GraphCanvas
    nodes={[{ id: attachment.activationId, label: attachment.nodeLabel, status: attachment.operationalState, x: 0, y: 0 }]}
    annotations={{ [attachment.activationId]: `Quality: ${projection.unresolvedCount} unresolved criteria` }}
    selection={attachment.activationId} select={() => inspect?.(attachment)} label="Quality-marked execution point" /></div>;
}

export function QualityExecutionDetails({ attachment, back }: { attachment: QualityAttachment; back(): void }) {
  return <section className="quality-execution-detail" aria-label="Pinned execution point">
    <p className="eyebrow">Proven assessment subject / execution output</p><h3>{attachment.nodeLabel}</h3>
    <dl><dt>Execution state</dt><dd>{attachment.operationalState}</dd><dt>Pinned campaign revision</dt><dd>{attachment.cut.revision}</dd>
      <dt>Output</dt><dd>{attachment.port}</dd><dt>Loaded membership</dt><dd>{attachment.complete ? "Complete for this output" : "Partial; other items have not been inspected"}</dd></dl>
    <p>The assessed subject exactly matches an artifact in this pinned output. Execution success does not settle the scientific questions.</p>
    <details><summary>Exact execution reference</summary><p>Run {attachment.cut.run_id}</p><p>Activation {attachment.activationId}</p><p>Plan {attachment.cut.plan_sha256}</p></details>
    <button onClick={back}>Return to quality points</button>
  </section>;
}
