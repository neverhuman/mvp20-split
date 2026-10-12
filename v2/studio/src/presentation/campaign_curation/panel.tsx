import { useCallback, useEffect, useId, useRef, useSyncExternalStore } from 'react';
import type { CurationModel } from '../../page_models/campaign_curation/model.js';
import type { CurationSelection } from '../../transport/campaign_curation/identity.js';
import { CapabilityDetail } from './detail.js';
import './style.css';

export function CurationPanel({ model, selection, invalid = false, synthetic, back }: {
  model: CurationModel; selection: CurationSelection | null; invalid?: boolean; synthetic: boolean; back: () => void;
}) {
  const listen = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(listen, () => model.snapshot);
  const detailId = useId(), heading = useRef<HTMLHeadingElement>(null), focusDetail = useRef(false);
  useEffect(() => {
    void model.setVisible(false); void model.select(selection);
    const visibility = () => { void model.setVisible(!document.hidden); };
    visibility(); document.addEventListener('visibilitychange', visibility);
    return () => { document.removeEventListener('visibilitychange', visibility); void model.setVisible(false); };
  }, [model, selection]);
  useEffect(() => {
    if (view.phase === 'ready' && view.record?.requests.length && view.detail.phase === 'idle') void model.inspect(0);
  }, [model, view.phase, view.record, view.detail.phase]);
  useEffect(() => {
    if (view.detail.phase === 'ready' && focusDetail.current) { focusDetail.current = false; heading.current?.focus(); }
  }, [view.detail]);
  const record = view.record, data = record?.data;
  const terminal = data && ['failed', 'indeterminate', 'abstained'].includes(data.receipt.phase);
  const inspect = (index: number) => { focusDetail.current = true; void model.inspect(index); };
  const message = invalid ? 'This proposed-revision link is invalid or ambiguous.' :
    view.phase === 'loading' ? 'Loading the recorded proposal...' : view.phase === 'missing' ? 'No revision record is available for this selection.' :
    view.phase === 'denied' ? 'This revision or its capability details are not available to this session.' :
    view.phase === 'failed' ? (view.reason === 'invalid_response' ? 'The recorded revision could not be verified.' : 'The revision service is temporarily unavailable.') :
    view.phase === 'stale' ? 'This record needs a fresh read.' : !selection ? 'No proposed revision is selected. Open a recorded revision from the next-campaign workflow.' : null;
  return <main className="curation-review" aria-label="Campaign revision review">
    <div className="curation-toolbar"><button onClick={back}>Back to next iteration</button>
      <button disabled={!selection || invalid || view.phase === 'loading'} onClick={() => void model.refresh()}>Refresh record</button></div>
    <div className="curation-title"><div><p className="curation-kicker">Next campaign · recorded proposal</p>
      <h1>What does the next campaign need?</h1><p>Inspect the model's requested tools and the evidence recorded for their fulfillment.</p></div>
      {record && <span className="curation-state">{record.status}</span>}
    </div>
    {synthetic && <p className="curation-synthetic">Synthetic engineering context · not a scientific validation</p>}
    {message && <p role="status" className="curation-message">{message}</p>}
    {data && <>
      <section className="curation-intent" aria-label="Recorded revision direction"><h2>Requested direction</h2><p>{data.specification.direction}</p>
        {data.proposal && <><h3>Recorded model explanation</h3><p>{data.proposal.rationale}</p></>}
      </section>
      <details className="curation-context"><summary>Context requested for this revision</summary>
        <p>These are the references requested at submission. They are not a record of every item the model consumed.</p>
        <dl><dt>Knowledge revisions</dt><dd>{data.specification.context.knowledge.length} explicitly requested</dd>
          <dt>Research questions / evidence needs</dt><dd>{data.specification.context.questions.length} / {data.specification.context.needs.length}</dd>
          <dt>Input artifacts</dt><dd>{data.specification.context.artifacts.length}</dd></dl>
        {data.specification.context.knowledge.length > 0 && <ul>{data.specification.context.knowledge.map(head =>
          <li key={head.snapshot.graph.graph_id}>{head.snapshot.graph.graph_id} · revision {head.snapshot.revision}</li>)}</ul>}
      </details>
      {record!.requests.length ? <div className="curation-layout">
        <section className="curation-request-list" aria-label="Requested capabilities"><h2>Requested capabilities <span>{record!.requests.length}</span></h2>
          <ol>{record!.requests.map(row => <li key={row.reference.request_id}><button aria-pressed={view.detail.index === row.index}
            aria-controls={detailId} onClick={() => inspect(row.index)}><span className="curation-number">{row.index + 1}</span>
            <span><strong>{row.purpose}</strong><small>{row.graphGap}</small></span></button></li>)}</ol>
        </section>
        <section id={detailId} className="curation-detail" aria-label="Capability inspection">
          {view.detail.phase === 'loading' && <p role="status">Loading capability details...</p>}
          {view.detail.phase === 'missing' && <p role="status">The original capability request is not available.</p>}
          {['failed', 'stale'].includes(view.detail.phase) && <><p role="status">Capability details could not be verified or are temporarily unavailable.</p>
            <button onClick={() => view.detail.index !== null && inspect(view.detail.index)}>Retry capability read</button></>}
          {view.detail.record && <CapabilityDetail ref={heading} record={view.detail.record}/>}
        </section>
      </div> : <section className="curation-message"><h2>{data.proposal ? 'No additional capabilities requested' : terminal ? 'No retained proposal' : 'Awaiting a retained proposal'}</h2>
        <p>{data.proposal ? 'This recorded outcome did not request new tools.' : terminal ? 'This recorded outcome has no model proposal. It will not restart automatically.' : 'No model proposal is recorded for this request yet.'}</p>
        {data.validated_draft && <p>Validated draft revision {data.validated_draft.revision}. Campaign launch is a separate step.</p>}
      </section>}
      <details className="curation-technical"><summary>Original revision and model usage</summary><dl>
        <dt>Recorded curation</dt><dd>{data.receipt.reference.curation_id}</dd><dt>Predecessor run</dt><dd>{data.specification.context.predecessor.run_id}</dd>
        <dt>Original draft</dt><dd>{data.specification.context.draft.draft_id} · revision {data.specification.context.draft.revision}</dd>
        <dt>Recorded state</dt><dd>{data.receipt.phase} · revision {data.receipt.revision}</dd><dt>Reason</dt><dd>{data.receipt.reason_code ?? 'None recorded'}</dd>
        {data.provider && <><dt>Input / output tokens</dt><dd>{data.provider.usage.input_tokens ?? 'unknown'} / {data.provider.usage.output_tokens ?? 'unknown'}</dd>
          <dt>Raw provider capture digest</dt><dd>{data.provider.output_sha256 ?? 'No capture recorded'}</dd></>}
      </dl></details>
    </>}
  </main>;
}
