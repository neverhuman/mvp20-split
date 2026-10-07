import { useCallback, useEffect, useSyncExternalStore } from 'react';
import type { NamedViewsModel } from '../page_models/named_views.js';
import type { GraphSnapshotPage } from '../contracts/observations.js';
import { scientificViews } from '../page_models/view_catalog.js';

export function NamedViews({ model, anchor }: { model: NamedViewsModel; anchor: GraphSnapshotPage['snapshot'] | null }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  useEffect(() => { void model.load(anchor); return () => { void model.load(null); }; }, [model, anchor]);
  return <details className="named-views">
    <summary>Named research views</summary>
    <p role="status">{view.phase === 'ready' ? `Runtime views verified at revision ${view.catalog!.page.cut.revision}.` : view.error?.message ?? 'Loading available views…'}</p>
    <div className="toolbar"><span>{view.catalog?.available('execution_topology') ? 'Execution graph available' : 'Execution graph capability unavailable'}</span>
      <button disabled={!view.catalog?.available('successor_lineage') || view.lineagePhase === 'loading'} onClick={() => void model.lineage()}>Inspect predecessor lineage</button></div>
    <ul>{scientificViews.map(item => <li key={item.id}>{item.label} — owned by {item.owner}; not supplied by this execution view.</li>)}</ul>
    {view.lineagePhase === 'loading' && <p role="status">Loading retained lineage…</p>}
    {view.lineagePhase === 'failed' && <p role="status">{view.error?.kind === 'unavailable' ? 'No retained predecessor lineage is available for this run.' : view.error?.message}</p>}
    {view.lineage && <section aria-label="Retained predecessor lineage">
      <h2>Predecessor campaign</h2>
      <p>Run {view.lineage.predecessor.run_id} · pinned revision {view.lineage.predecessor.revision}</p>
      <p className="identity">Plan {view.lineage.predecessor.plan_sha256}</p>
      <p>{view.lineage.carried.length} explicit carried bindings. This is execution provenance, not scientific validation.</p>
      <ul>{view.lineage.carried.map(binding => <li key={binding.target_port}>{binding.source.kind === 'node_output' ? `Activation ${binding.source.activation_id}` : 'Run output'}
        {' '}{binding.source.port} → {binding.target_port}</li>)}</ul>
    </section>}
  </details>;
}
