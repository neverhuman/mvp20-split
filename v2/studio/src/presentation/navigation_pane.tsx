import { useCallback, useMemo, useSyncExternalStore } from 'react';
import type { NavigationModel } from '../page_models/navigation.js';
import type { MonitorModel, MonitorView } from '../page_models/monitor.js';
import { SceneWindow } from '../page_models/scene.js';
import { GraphCanvas } from './graph_canvas.js';
import { MonitorDetail } from './monitor_detail.js';
import type { NamedViewsModel } from '../page_models/named_views.js';
import { NamedViews } from './named_views.js';
import type { EvidenceModel } from '../page_models/evidence.js';
import { EvidencePane } from './evidence_pane.js';

export function NavigationPane({ navigation, monitor, observation, namedViews, evidence }: {
  navigation: NavigationModel; monitor: MonitorModel; observation: MonitorView; namedViews?: NamedViewsModel; evidence?: EvidenceModel;
}) {
  const subscribe = useCallback((notify: () => void) => navigation.subscribe(notify), [navigation]);
  const view = useSyncExternalStore(subscribe, () => navigation.snapshot);
  const offset = view.offset;
  const anchor = (observation.phase === 'ready' || observation.phase === 'empty') ? observation.window?.snapshot : null;
  const page = view.topology?.page;
  const scene = useMemo(() => {
    const result = new SceneWindow();
    if (!page) return result;
    const start = offset < page.nodes.length ? offset : 0;
    const slice = page.nodes.slice(start, start + result.limit);
    const ids = new Set(slice.map(node => node.activation.activation_id));
    result.replace({ nodes: slice.map(({ activation: node }, index) => ({ id: node.activation_id,
      label: node.path.node_id, status: node.status, x: (index % 4) * 245, y: Math.floor(index / 4) * 100 })),
      edges: (view.topology?.visibleEdges ?? []).filter(edge => ids.has(edge.source) && ids.has(edge.target))
        .map(edge => ({ ...edge, id: `${edge.source}:${edge.route}:${edge.target}` })),
      offset: start, total: page.node_count });
    return result;
  }, [view.topology, offset]);
  const select = useCallback((id: string) => { void monitor.select(id); }, [monitor]);
  const parent = view.scopes?.parent_activation_id ?? undefined;
  return <section aria-label="Authored graph navigation">
    {namedViews && <NamedViews model={namedViews} anchor={anchor ?? null} />}
    <div className="toolbar">
      <button onClick={() => void navigation.scopes()} disabled={!anchor}>Root groups</button>
      <span>Revision {page?.cut.revision ?? anchor?.cut.revision ?? 'unavailable'} · Read-only authored connections</span>
    </div>
    {page && <p>Occurrence: {page.graph_scope.occurrences.length ? page.graph_scope.occurrences.map(item => `${item.node_id} [${item.index}]`).join(' / ') : 'root graph'}
      {view.scopes && !view.scopes.scopes.some(scope => scope.scope_key === page.graph_scope.scope_key) ? ' · selected group is outside the loaded group page' : ''}</p>}
    {observation.selection && !scene.nodes.some(node => node.id === observation.selection) && <p>Selected activation is outside this window.</p>}
    <p role="status" data-testid="navigation-status">{view.error?.message ?? (view.phase === 'loading' ? 'Loading occurrence groups…' :
      view.topologyPhase === 'loading' ? 'Loading authored topology…' : page ?
      `${scene.nodes.length} nodes shown · ${scene.omitted} outside this window · ${view.topology!.unresolvedEdges} links await an unloaded target` :
      'Choose an occurrence group to explore its authored graph.')}</p>
    <div className="work-area">
      <GraphCanvas nodes={scene.nodes} edges={scene.edges} selection={observation.selection} select={select}
        initialViewport={view.viewport} rememberViewport={viewport => navigation.setViewport(viewport)} />
      <aside className="navigation-inspector" aria-label="Occurrence navigator">
        <MonitorDetail view={observation} />
        {evidence && <EvidencePane model={evidence} monitor={monitor} observation={observation} />}
        <h2>Occurrence groups</h2>
        <ul className="node-list" aria-label="Occurrence groups">{view.scopes?.scopes.map(scope => <li key={scope.scope_key}>
          <button onClick={() => void navigation.open(scope.scope_key)}>
            <span>{scope.occurrences.length ? scope.occurrences.map(item => `${item.node_id} [${item.index}]`).join(' / ') : 'Root graph'}</span>
            <small>{scope.status} · {scope.node_count} nodes</small>
          </button></li>)}</ul>
        <button disabled={!view.scopes?.next_cursor || view.phase === 'loading'} onClick={() => void navigation.scopes(parent, true)}>Next groups</button>
        <h2>Nodes in this window</h2>
        <ul className="node-list" aria-label="Topology nodes">{scene.nodes.map(node => {
          const record = page!.nodes.find(item => item.activation.activation_id === node.id)!;
          return <li key={node.id}><button aria-pressed={observation.selection === node.id} onClick={() => select(node.id)}>
            <span>{node.label}</span><small>{node.status}</small></button>
            <button onClick={() => void navigation.open(page!.graph_scope.scope_key, { focus_activation_id: node.id, radius: 1 })}>Neighborhood of {node.label}</button>
            {record.child_scope_count > 0 && <button onClick={() => void navigation.scopes(node.id)}>Open {record.child_scope_count} child groups of {node.label}</button>}
            {(record.activation.kind === 'iterate' || record.activation.kind === 'scatter') && record.child_scope_count === 0 &&
              <p>No occurrence groups instantiated yet; the nested definition is not expanded in this observation.</p>}
          </li>;
        })}</ul>
        <div className="pages">
          <button disabled={!page?.next_cursor || view.loadingMore || view.topologyPhase !== 'ready'} onClick={() => void navigation.more()}>Load topology page</button>
          <button disabled={offset === 0} onClick={() => navigation.setOffset(0)}>First window</button>
          <button disabled={!page || offset + scene.limit >= page.nodes.length} onClick={() => navigation.setOffset(offset + scene.limit)}>Next window</button>
        </div>
        <h2>Authored links in this window</h2>
        <ul>{scene.edges.map(edge => <li key={edge.id}>{scene.nodes.find(node => node.id === edge.source)?.label} → {scene.nodes.find(node => node.id === edge.target)?.label}
          {' '}({page!.edges.find(item => `${item.source}:${item.route}:${item.target}` === edge.id)?.route})</li>)}</ul>
        <p>Execution status is not scientific acceptance. Layout cannot alter a campaign.</p>
      </aside>
    </div>
  </section>;
}
