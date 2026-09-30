import type { MonitorView } from '../page_models/monitor.js';

export function MonitorDetail({ view }: { view: MonitorView }) {
  return <section className="inspector" aria-label="Selected node" aria-busy={view.detailPhase === 'loading'}>
    <p className="eyebrow">Selected activation</p>
    {!view.selection ? <><h2>Follow an activation</h2><p>Select on the canvas or use the list.</p></> :
      view.detailPhase === 'loading' ? <p role="status">Loading selected detail…</p> :
      view.detail ? <><h2>{view.detail.node.path.node_id}</h2><p className="outcome">{view.detail.node.status}</p>
        <p>Observation revision {view.detail.cut.revision}</p><p>{view.detail.attempts.length} attempts loaded · {view.detail.outputs.length} output summaries</p>
        {view.detail.next_cursor && <p>Additional attempts are outside this detail page.</p>}
        {view.detail.node.reason_code && <p>Outcome: {view.detail.node.reason_code}</p>}
        <p className="muted">Execution status does not establish scientific acceptance.</p></> :
      <p role="status">{view.detailPhase === 'denied' ? 'Access to this detail is denied.' : view.detailError?.message ?? 'Detail is not current. Refresh the observation.'}</p>}
  </section>;
}
