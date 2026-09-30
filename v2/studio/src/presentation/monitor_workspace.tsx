import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from 'react';
import type { MonitorModel } from '../page_models/monitor.js';
import type { RunContext } from '../page_models/graph_window.js';
import { SceneWindow } from '../page_models/scene.js';
import { GraphCanvas } from './graph_canvas.js';
import { MonitorDetail } from './monitor_detail.js';
import type { NavigationModel } from '../page_models/navigation.js';
import type { NamedViewsModel } from '../page_models/named_views.js';
import { NavigationPane } from './navigation_pane.js';
import type { EvidenceModel } from '../page_models/evidence.js';
import { EvidencePane } from './evidence_pane.js';
import './style.css';

export function MonitorWorkspace({ model, context, synthetic = false, navigation, namedViews, evidence }: { model: MonitorModel; context: RunContext; synthetic?: boolean; navigation?: NavigationModel; namedViews?: NamedViewsModel; evidence?: EvidenceModel }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const [filter, setFilter] = useState('');
  const [topology, setTopology] = useState(false);
  useEffect(() => { void model.open(context); }, [model, context.scope.tenant_id, context.scope.project_id, context.run]);
  useEffect(() => {
    const visibility = () => { void model.setVisible(document.visibilityState === 'visible'); };
    document.addEventListener('visibilitychange', visibility); visibility();
    return () => document.removeEventListener('visibilitychange', visibility);
  }, [model]);
  const scene = useMemo(() => {
    const result = new SceneWindow();
    if (view.window) result.replace({ nodes: view.window.nodes.slice(0,200).map((node,index) => ({ id: node.activation_id, label: node.path.node_id,
      status: node.status, x: (index%4)*245, y: Math.floor(index/4)*100 })), edges: [], offset: 0, total: view.window.snapshot.node_count });
    return result;
  }, [view.window]);
  const shown = scene.nodes.filter(node => node.label.toLowerCase().includes(filter.toLowerCase()));
  const current = view.phase === 'ready' || view.phase === 'empty';
  const select = useCallback((id: string) => { void model.select(id); }, [model]);
  return <div className="workspace">
    <header><span className="brand">AMPHORA<span>research studio</span></span><div className="mode">Monitor</div><span className="fixture">{synthetic ? 'Synthetic observation fixture' : 'Campaign observations'}</span></header>
    <main>
      <div className="context"><div><p className="eyebrow">Campaign / execution observations</p><h1>Follow execution</h1></div><p>Read-only · {view.window ? `revision ${view.window.snapshot.cut.revision}` : 'awaiting observation'}</p></div>
      <div className="toolbar">{!topology && <><label htmlFor="node-filter">Find in loaded nodes</label><input id="node-filter" value={filter} onChange={event => setFilter(event.target.value)} maxLength={120} /></>}
        <button onClick={() => void model.refresh()} disabled={view.phase === 'loading'}>Refresh observation</button>
        <button onClick={() => void model.poll()} disabled={!current}>Check for updates</button></div>
      {!topology && <p className="status" role="status" data-testid="graph-status">{view.phase === 'loading' ? 'Loading observation… Previous records are not current.' :
        view.phase === 'denied' ? 'Access denied. Observation data has been cleared.' : view.phase === 'stale' ? 'Observation expired or changed. Refresh to continue.' :
        view.phase === 'failed' ? `Observation unavailable. ${view.error?.message ?? ''}` : view.phase === 'empty' ? 'No activations in this scope.' :
        `${shown.length} shown · ${scene.omitted} outside this window · ${scene.nodes.length - shown.length} filtered from this window`}</p>}
      {navigation && <div className="toolbar" aria-label="Observation view">
        <button aria-pressed={!topology} onClick={() => setTopology(false)}>Activation inventory</button>
        <button aria-pressed={topology} onClick={() => setTopology(true)}>Authored graph</button>
      </div>}
      {topology && navigation ? <NavigationPane navigation={navigation} monitor={model} observation={view} {...(namedViews ? { namedViews } : {})} {...(evidence ? { evidence } : {})} /> : <div className="work-area" data-phase={view.phase}>
        <GraphCanvas nodes={shown} selection={view.selection} select={select} />
        <aside className={evidence ? 'navigation-inspector' : undefined} aria-label="Node navigator"><MonitorDetail view={view} />
          {evidence && <EvidencePane model={evidence} monitor={model} observation={view} />}
          <div className="list-heading"><h2>Loaded activations</h2><span>{shown.length}</span></div>
          <ul className="node-list" aria-label="Loaded activation list">{shown.map(node => <li key={node.id}><button data-node-id={node.id} disabled={!current} aria-pressed={view.selection === node.id} onClick={() => select(node.id)}><span>{node.label}</span><small>{node.status}</small></button></li>)}</ul>
          <div className="pages"><button disabled={!current || view.loadingMore || !view.window?.next || scene.nodes.length >= scene.limit} onClick={() => void model.loadMore()}>{view.loadingMore ? 'Loading more…' : 'Load next page'}</button></div>
          {scene.nodes.length >= scene.limit && scene.omitted > 0 && <p className="bounded-note">Scene limit reached. Narrower scope navigation is not yet available.</p>}
        </aside>
      </div>}
      {view.window && <details className="named-views" aria-label="Campaign observation">
        <summary>Campaign {view.window.snapshot.cut.run_id}</summary>
        <p>Execution {view.window.snapshot.status} · revision {view.window.snapshot.cut.revision} · frontier {view.window.snapshot.cut.frontier_revision}</p>
        <p>Attempt budget: {view.window.snapshot.budget.spent} spent, {view.window.snapshot.budget.reserved} reserved, {view.window.snapshot.budget.limit} limit.</p>
        <p className="identity">Plan {view.window.snapshot.cut.plan_sha256}</p>
        <p>{view.window.snapshot.cut.scope.tenant_id} / {view.window.snapshot.cut.scope.project_id}</p>
        <p>{current ? 'Current observation.' : 'This observation is not current.'} Scientific acceptance is a separate domain decision.</p>
      </details>}
      <footer>{topology ? "Authored links from the retained campaign plan. Execution status does not establish scientific acceptance." : "Activation inventory; this endpoint does not publish connections. Layout cannot change a campaign."}</footer>
    </main>
  </div>;
}
