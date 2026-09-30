import { useCallback, useEffect, useSyncExternalStore } from 'react';
import type { EvidenceModel } from '../page_models/evidence.js';
import type { MonitorModel, MonitorView } from '../page_models/monitor.js';

export function EvidencePane({ model, monitor, observation }: { model: EvidenceModel; monitor: MonitorModel; observation: MonitorView }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const detail = observation.detailPhase === 'ready' ? observation.detail : null;
  const anchor = observation.phase === 'ready' ? observation.window?.snapshot : null;
  useEffect(() => { model.bind(anchor ?? null, detail); return () => model.bind(null, null); }, [model, anchor, detail]);
  const record = view.completion.value, metadata = view.artifact.value;
  const occurrences = detail?.node.path.occurrences ?? [];
  const blocked = Object.values(view).some(region => region.phase === 'denied' || region.phase === 'stale');
  return <section className="evidence-inspector" aria-label="Linked execution evidence">
    <h2>Execution evidence</h2>
    {!detail ? <p>Select a current activation to inspect its retained evidence.</p> : <>
      <p>Occurrence: {occurrences.length ? occurrences.map(item => `${item.node_id} [${item.index}]`).join(' / ') : 'root graph'}</p>
      <h3>Attempts in this page</h3>
      <ul>{detail.attempts.map(attempt => <li key={attempt.attempt_id}>
        <button disabled={blocked || !attempt.completion_id} onClick={() => void model.completion(attempt.attempt_id)}>Inspect attempt {attempt.attempt_id}</button>
        <p>{attempt.status} · fence {attempt.fence} · {attempt.canonical_result ? 'canonical execution result' : 'not canonical'}</p>
      </li>)}</ul>
      {!detail.attempts.length && <p>No attempts recorded for this activation.</p>}
      <div className="pages"><button disabled={!detail.next_cursor} onClick={() => void monitor.nextAttempts()}>Next attempts</button>
        <button onClick={() => void monitor.select(detail.node.activation_id)}>First attempts</button></div>
      <h3>Node outputs</h3>
      <ul>{detail.outputs.map(output => <li key={output.port}>
        <button disabled={blocked} onClick={() => void model.values(output.port)}>Inspect output {output.port}</button>
        <p>{output.kind} · {output.item_count} members · {output.missing_count} missing</p>
      </li>)}</ul>
    </>}
    {Object.entries(view).map(([name, region]) => region.phase === 'loading' ? <p role="status" key={name}>Loading {name}…</p> :
      region.error ? <p role="status" key={name}>{name}: {region.error.message}</p> : null)}
    {record && <section aria-label="Retained completion">
      <h3>Retained completion</h3><p>{record.completion_id} · Runtime revision {record.accepted_run_revision}</p>
      <p>{record.result.outcome.status} · {record.canonical_result ? 'canonical execution result' : 'noncanonical report'}</p>
      <p>{record.retention_reservation_ids?.length ?? 0} retention reservations recorded.</p>
    </section>}
    {view.values.value && <section aria-label="Output members">
      <h3>Output members</h3><ul>{view.values.value.items.map(item => <li key={item.index}>
        {item.index}: {item.value.kind === 'artifact' ? item.value.artifact.artifact_id : item.value.kind === 'missing' ?
          `Missing: ${item.value.reason_code}` : String(item.value.value)}
      </li>)}</ul><p>{view.values.value.items.length} members in this page of {view.values.value.item_count}.</p>
      <button disabled={!view.values.value.next_cursor} onClick={() => void model.values(view.values.value!.port, true)}>Next output members</button>
    </section>}
    {model.references().length > 0 && <section aria-label="Linked artifacts"><h3>Linked artifacts</h3>
      <ul>{model.references().map(ref => <li key={`${ref.artifact_id}:${ref.sha256}`}>
        <button onClick={() => void model.artifact(ref)}>Inspect artifact {ref.artifact_id}</button>
      </li>)}</ul></section>}
    {metadata && <section aria-label="Verified artifact metadata"><h3>Artifact metadata</h3>
      <p>{metadata.artifact_id} · {metadata.size_bytes} bytes · {metadata.media_type}</p>
      <p>Schema {metadata.schema_ref.schema_id} / {metadata.schema_ref.version}</p>
      <p className="identity">SHA-256 {metadata.sha256}</p><p>Metadata matches the retained reference. Artifact content has not been downloaded.</p>
    </section>}
    <p>Runtime retention and tool success do not establish scientific acceptance.</p>
  </section>;
}
