import { useCallback, useEffect, useMemo, useSyncExternalStore } from 'react';
import type { NavigationModel } from '../page_models/navigation.js';
import type { MonitorModel, MonitorView } from '../page_models/monitor.js';
import { SceneWindow } from '../page_models/scene.js';
import { GraphCanvas } from './graph_canvas.js';
import { MonitorDetail } from './monitor_detail.js';
import type { NamedViewsModel } from '../page_models/named_views.js';
import { NamedViews } from './named_views.js';
import type { EvidenceModel } from '../page_models/evidence.js';
import { inlineScene } from '../page_models/inline_scopes/projection.js';
import { EvidencePane } from './evidence_pane.js';

export function NavigationPane({ navigation, monitor, observation, namedViews, evidence, inline = false }: {
  navigation: NavigationModel; monitor: MonitorModel; observation: MonitorView; namedViews?: NamedViewsModel; evidence?: EvidenceModel; inline?: boolean;
}) {
  const subscribe = useCallback((notify: () => void) => navigation.subscribe(notify), [navigation]);
  const view = useSyncExternalStore(subscribe, () => navigation.snapshot);
  const inlineSubscribe = useCallback((notify:()=>void)=>navigation.inline.subscribe(notify),[navigation]);
  const groups = useSyncExternalStore(inlineSubscribe,()=>navigation.inline.snapshot);
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
  const expanded = useMemo(()=>inline && page ? inlineScene(page,groups) : null,[inline,page,groups]);
  const shown = expanded ?? scene;
  const focusGroup = Object.entries(groups).filter(([id,g])=>g.phase==='ready' && expanded?.records.some(r=>r.activation.activation_id===id)).at(-1);
  const focusNodes = focusGroup ? [focusGroup[0], ...focusGroup[1].pages.flatMap(p=>p.nodes.map(n=>n.activation.activation_id)), '@scope-end:'+focusGroup[0]] : undefined;
  const viewKey = (page?.graph_scope.scope_key ?? 'unloaded') + (inline ? ':'+Object.keys(groups).filter(id=>groups[id]?.phase==='ready').sort().join(',') : '');
  useEffect(()=>{
    if(inline && page) navigation.inline.restore(expanded?.records??page.nodes,!page.graph_scope.occurrences.length);
  },[inline,page,navigation,expanded]);
  const select = useCallback((id: string) => { void monitor.select(expanded?.owners[id] ?? id); }, [monitor,expanded]);
  const parent = view.scopes?.parent_activation_id ?? undefined;
  return <section aria-label="Authored graph navigation">
    {namedViews && <NamedViews model={namedViews} anchor={anchor ?? null} />}
    <div className="scope-summary"><div className="toolbar">
      <button onClick={() => void navigation.root()} disabled={!anchor}>Return to root graph</button>
      <span>Revision {page?.cut.revision ?? anchor?.cut.revision ?? 'unavailable'} · Read-only authored connections</span>
    </div>
    {page && <p>Occurrence: {page.graph_scope.occurrences.length ? page.graph_scope.occurrences.map(item => `${item.node_id} [${item.index}]`).join(' / ') : 'root graph'}
      {view.scopes && !view.scopes.scopes.some(scope => scope.scope_key === page.graph_scope.scope_key) ? ' · selected group is outside the loaded group page' : ''}</p>}
    {observation.selection && !shown.nodes.some(node => node.id === observation.selection) && <p>Selected activation is outside this window.</p>}
    <p role="status" data-testid="navigation-status">{view.error?.message ?? (view.phase === 'loading' ? 'Loading occurrence groups…' :
      view.topologyPhase === 'loading' ? 'Loading authored topology…' : page ?
      `${shown.nodes.length} nodes shown · ${scene.omitted} outside this window · ${view.topology!.unresolvedEdges} links await an unloaded target` :
      'Choose an occurrence group to explore its authored graph.')}</p>
    </div>
    {inline && <section className="inline-scope-controls" aria-label="Parallel work and iterations">
      <p><strong>Parallel branches stay side by side.</strong> Solid lines: authored links. Dashed lines: group entry, completion and continuation.</p>
      <p className="muted">Node states are from this observation. Parallel structure does not prove simultaneous execution.</p>
      <div className="toolbar">{(expanded?.records ?? []).filter(n=>n.child_scope_count>0).map(record=>{
        const id=record.activation.activation_id,group=groups[id];
        const occurrence=record.activation.path.occurrences?.map(o=>`${o.node_id} ${o.index+1}`).join(' / ');
        return <button key={id} disabled={group?.phase==='loading' || !group && Object.keys(groups).length>=8} aria-expanded={group?.phase==='ready'} onClick={()=>group?.phase==='ready'?navigation.inline.collapse(id):void navigation.inline.expand(record)}>
          {group?.phase==='ready'?'Collapse':group?.phase==='loading'?'Loading':'Expand'} {record.activation.path.node_id}{occurrence?' / '+occurrence:''} ({record.child_scope_count} {record.activation.kind==='scatter'?'parallel branches':'iterations'})
        </button>;
      })}</div>
      {Object.keys(groups).length>=8 && <p role="status">Eight groups loaded. Collapse a group before expanding another.</p>}
      {expanded?.notes.map(note=><p role="status" key={note}>{note}</p>)}
    </section>}
    <div className="work-area">
      <GraphCanvas key={viewKey} minimap={inline} focusNodes={inline ? focusNodes : undefined} nodes={shown.nodes} edges={shown.edges} selection={observation.selection} select={select}
        annotations={expanded?.annotations ?? Object.fromEntries((page?.nodes ?? []).filter(node => node.child_scope_count > 0).map(node =>
          [node.activation.activation_id, `${node.child_scope_count} ${node.activation.kind === 'scatter' ? 'parallel branches' : 'iterations'} available`]))}
        initialViewport={page ? navigation.viewportFor(viewKey) : undefined} rememberViewport={viewport => navigation.setViewport(viewport,viewKey)} />
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
        <ul className="node-list" aria-label="Topology nodes">{shown.nodes.filter(node=>!node.id.startsWith('@scope-end:')).map(node => {
          const record = (expanded?.records ?? page!.nodes).find(item => item.activation.activation_id === node.id)!;
          return <li key={node.id}><button aria-pressed={observation.selection === node.id} onClick={() => select(node.id)}>
            <span>{node.label}</span><small>{node.status}</small></button>
            <button disabled={inline && !page!.nodes.some(n=>n.activation.activation_id===node.id)} onClick={() => void navigation.open(page!.graph_scope.scope_key, { focus_activation_id: node.id, radius: 1 })}>Neighborhood of {node.label}</button>
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
        <ul>{shown.edges.map(edge => <li key={edge.id}>{shown.nodes.find(node => node.id === edge.source)?.label} → {shown.nodes.find(node => node.id === edge.target)?.label}
          {' '}({edge.label === 'scope-boundary' ? 'group boundary' : 'authored control'})</li>)}</ul>
        <p>Execution status is not scientific acceptance. Layout cannot alter a campaign.</p>
      </aside>
    </div>
  </section>;
}
