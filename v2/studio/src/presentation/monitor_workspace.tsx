import type { SupervisionModel } from "../page_models/supervision/model.js";
import { SupervisionInspector } from "./supervision/inspector.js";
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
import { InspectionHistory } from '../page_models/inspection_history.js';
import { PinnedInspection } from './inspection_pin.js';
import type { EmergencyStop } from '../page_models/design/emergency_stop.js';
import { EmergencyControl } from './emergency_control.js';
import './style.css';

export function MonitorWorkspace({ model, context, synthetic = false, active = true, navigation, namedViews, evidence, emergency, supervision }: { model: MonitorModel; context: RunContext; synthetic?: boolean; active?: boolean; navigation?: NavigationModel; namedViews?: NamedViewsModel; evidence?: EvidenceModel; emergency?: EmergencyStop; supervision?: SupervisionModel }) {
  const subscribe = useCallback((notify: () => void) => model.subscribe(notify), [model]);
  const view = useSyncExternalStore(subscribe, () => model.snapshot);
  const [filter, setFilter] = useState('');
  const [visible, setVisible] = useState(true);
  const [topology, setTopology] = useState(false);
  const [inspectingCheckpoints, setInspectingCheckpoints] = useState(false);
  useEffect(() => { supervision?.bind(context); setInspectingCheckpoints(false); }, [supervision, context.scope.tenant_id, context.scope.project_id, context.run]);
  useEffect(() => { if (!visible || !inspectingCheckpoints) supervision?.invalidate(); }, [supervision, visible, inspectingCheckpoints]);

  const history = useMemo(() => new InspectionHistory(), []);
  const historySubscribe = useCallback((notify: () => void) => history.subscribe(notify), [history]);
  const historyView = useSyncExternalStore(historySubscribe, () => history.snapshot);
  const pin = history.compatible(context.scope) && view.phase !== 'denied' && view.detailPhase !== 'denied' ? historyView.pins.find(item => item.id === historyView.selected) : undefined;
  useEffect(() => {
    if (view.phase === 'denied' || view.detailPhase === 'denied') history.deny(); else history.setScope(context.scope);
  }, [history, context.scope.tenant_id, context.scope.project_id, view.phase, view.detailPhase]);
  useEffect(() => {
    const check = () => {
      if (navigation?.snapshot.phase === 'denied' || namedViews?.snapshot.phase === 'denied' ||
        Object.values(evidence?.snapshot ?? {}).some(region => region.phase === 'denied')) history.deny();
    };
    const subscriptions = [navigation?.subscribe(check), namedViews?.subscribe(check), evidence?.subscribe(check)];
    return () => { for (const unsubscribe of subscriptions) unsubscribe?.(); };
  }, [history, navigation, namedViews, evidence]);
  useEffect(() => { void model.open(context); }, [model, context.scope.tenant_id, context.scope.project_id, context.run]);
  useEffect(() => {
    const visibility = () => { const shown = active && document.visibilityState === 'visible'; setVisible(shown); void model.setVisible(shown); };
    document.addEventListener('visibilitychange', visibility); visibility();
    return () => { document.removeEventListener('visibilitychange', visibility); void model.setVisible(false); };
  }, [model, active]);
  useEffect(() => {
    const current = view.phase === 'ready' || view.phase === 'empty';
    void navigation?.observe(current ? view.window?.snapshot ?? null : null, visible && topology && !pin, view.phase === 'denied');
  }, [navigation, view.window?.snapshot, view.phase, visible, topology, pin]);
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
      <div className="context"><div><p className="eyebrow">Campaign / execution observations</p><h1>Follow execution</h1></div><p>Read-only · {view.window ? `${current ? 'live' : 'retained'} revision ${view.window.snapshot.cut.revision}` : 'awaiting observation'}</p></div>
      <div className="toolbar">{!topology && !pin && <><label htmlFor="node-filter">Find in loaded nodes</label><input id="node-filter" value={filter} onChange={event => setFilter(event.target.value)} maxLength={120} /></>}
        <button onClick={() => void model.refresh()} disabled={view.phase === 'loading'}>Refresh observation</button>
        <button onClick={() => void model.poll()} disabled={!current}>Check for updates</button>
        {emergency?.matches(context) && <a href="#emergency-control">Emergency control</a>}</div>
      {!topology && !pin && <p className="status" role="status" data-testid="graph-status">{view.phase === 'loading' ? 'Loading observation… Previous records are not current.' :
        view.phase === 'denied' ? 'Access denied. Observation data has been cleared.' : view.phase === 'stale' ? 'Observation expired or changed. Refresh to continue.' :
        view.phase === 'failed' ? `Observation unavailable. ${view.error?.message ?? ''}` : view.phase === 'empty' ? 'No activations in this scope.' :
        `${shown.length} shown · ${scene.omitted} outside this window · ${scene.nodes.length - shown.length} filtered from this window`}</p>}
      <div className="toolbar" aria-label="Inspection history">
        <button disabled={!current || !!pin || !history.compatible(context.scope)} onClick={() => history.capture({ monitor: view,
          ...(topology && navigation ? { navigation: navigation.snapshot } : {}), ...(evidence ? { evidence: evidence.snapshot } : {}),
          ...(namedViews ? { namedViews: namedViews.snapshot } : {}) })}>Pin loaded inspection</button>
        <label htmlFor="inspection-history">Inspect</label><select id="inspection-history" value={pin?.id ?? ''} onChange={event => history.select(event.target.value || null)}>
          <option value="">Live observation</option>{history.compatible(context.scope) && historyView.pins.map(item => <option key={item.id} value={item.id}>{item.cut.run_id} / revision {item.cut.revision} / {item.id}</option>)}
        </select>{pin && <button onClick={() => history.remove(pin.id)}>Remove pin</button>}
        {historyView.error && <p role="alert">{historyView.error}</p>}
      </div>
      {navigation && <div className="toolbar" aria-label="Observation view">
        <button aria-pressed={!topology} onClick={() => { history.select(null); setTopology(false); }}>Activation inventory</button>
        <button aria-pressed={topology} onClick={() => { history.select(null); setTopology(true); }}>Authored graph</button>
      </div>}
      {supervision && <button aria-pressed={inspectingCheckpoints} onClick={() => { history.select(null); setInspectingCheckpoints(!inspectingCheckpoints); if (!inspectingCheckpoints) void supervision.refresh(); }}>{inspectingCheckpoints ? 'Return to execution graph' : 'Inspect checkpoint reasoning'}</button>}
      {inspectingCheckpoints && supervision ? <SupervisionInspector model={supervision} /> : pin ? <PinnedInspection key={pin.id} pin={pin} /> : topology && navigation ? <NavigationPane navigation={navigation} monitor={model} observation={view} {...(namedViews ? { namedViews } : {})} {...(evidence ? { evidence } : {})} /> : <div className="work-area" data-phase={view.phase}>
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
        {view.fetchedAt && <p>Snapshot fetched <time dateTime={view.fetchedAt}>{view.fetchedAt}</time>. Fetch time is separate from the source revision.</p>}
        <p>Attempt budget: {view.window.snapshot.budget.spent} spent, {view.window.snapshot.budget.reserved} reserved, {view.window.snapshot.budget.limit} limit.</p>
        <p className="identity">Plan {view.window.snapshot.cut.plan_sha256}</p>
        <p>{view.window.snapshot.cut.scope.tenant_id} / {view.window.snapshot.cut.scope.project_id}</p>
        <p>{current ? 'Current observation.' : 'This observation is not current.'} Scientific acceptance is a separate domain decision.</p>
      </details>}
      {emergency?.matches(context) && <EmergencyControl model={emergency} observation={current && !pin ? view.window?.snapshot ?? null : null} denied={view.phase === 'denied'} />}
      <footer>{topology ? "Authored links from the retained campaign plan. Execution status does not establish scientific acceptance." : "Activation inventory; this endpoint does not publish connections. Layout cannot change a campaign."}</footer>
    </main>
  </div>;
}
