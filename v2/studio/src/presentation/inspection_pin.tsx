import { useState } from 'react';
import type { InspectionPin } from '../page_models/history_pin.js';
import { GraphCanvas } from './graph_canvas.js';

/** Captured data only. Selecting another node never starts a historical read. */
export function PinnedInspection({ pin }: { pin: InspectionPin }) {
  const [selection, select] = useState(pin.selection);
  const detail = pin.detail?.node.activation_id === selection ? pin.detail : null;
  return <section aria-label="Pinned inspection">
    <p className="status" role="status">Historical pin · revision {pin.cut.revision} · {pin.nodes.length} captured · {pin.totalNodes - pin.nodes.length} outside this capture</p>
    <p className="bounded-note">Captured {pin.capturedAt}. This local snapshot stays fixed. Unloaded records are unavailable in this pin.</p>
    <div className="work-area">
      <GraphCanvas nodes={pin.nodes.map((node, index) => ({ id: node.activation_id, label: node.path.node_id, status: node.status,
        x: index % 4 * 245, y: Math.floor(index / 4) * 100 }))}
        edges={pin.edges.map(edge => ({ id: `${edge.source}:${edge.target}:${edge.route}`, source: edge.source, target: edge.target }))}
        selection={selection} select={select} initialViewport={pin.viewport} />
      <aside className="navigation-inspector" aria-label="Captured records">
        <h2>Captured nodes</h2>
        <ul className="node-list">{pin.nodes.map(node => <li key={node.activation_id}><button aria-pressed={selection === node.activation_id}
          onClick={() => select(node.activation_id)}><span>{node.path.node_id}</span><small>{node.status}</small></button></li>)}</ul>
        {detail ? <><h2>{detail.node.path.node_id}</h2>
          {!pin.nodes.some(node => node.activation_id === detail.node.activation_id) && <p>Selected detail is outside the captured graph window.</p>}
          <p>{detail.node.status} · {detail.attempts.length} captured attempts · {detail.outputs.length} output summaries</p>
          {pin.completion && <p>Retained completion: {pin.completion.completion_id} · {pin.completion.result.outcome.status}</p>}
          {pin.values && <p>Captured output page: {pin.values.items.length} values for {pin.values.port}</p>}
          {pin.artifact && <p className="identity">Artifact metadata: {pin.artifact.artifact_id} · {pin.artifact.sha256}</p>}
        </> : <p>Detail for this selection was not captured.</p>}
        {pin.lineage && <p>Retained predecessor: {pin.lineage.predecessor.run_id}</p>}
        <p>Execution status does not establish scientific acceptance.</p>
      </aside>
    </div>
  </section>;
}
