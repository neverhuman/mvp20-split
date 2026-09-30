import { useCallback, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { SceneWindow, type ScenePage } from '../../src/page_models/scene.js';
import { FlowCanvas, CyCanvas } from './renderers.js';
import '../../src/presentation/style.css';

declare global { interface Window { spike: { scene: SceneWindow; ready: boolean; revision: number; renderer: string } } }

function Workspace() {
  const [scene] = useState(() => new SceneWindow());
  const [revision, setRevision] = useState(0);
  const [phase, setPhase] = useState('loading');
  const [query, setQuery] = useState('');
  const [renderer, setRenderer] = useState(new URLSearchParams(location.search).get('renderer') === 'cytoscape' ? 'cytoscape' : 'reactflow');
  const controller = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const load = useCallback(async (filter: string, offset: number) => {
    controller.current?.abort(); const request = new AbortController(); controller.current = request;
    const ticket = ++generation.current; setPhase('loading');
    try {
      const response = await fetch(`/fixture/scene?q=${encodeURIComponent(filter)}&offset=${offset}`, { signal: request.signal });
      if (!response.ok) throw new Error('Fixture unavailable');
      const page = await response.json() as ScenePage;
      if (ticket !== generation.current) return;
      scene.replace(page); setRevision(r => r + 1); setPhase(page.total ? 'ready' : 'empty');
    } catch { if (ticket === generation.current && !request.signal.aborted) setPhase('failed'); }
  }, [scene]);
  useEffect(() => { void load('', 0); return () => controller.current?.abort(); }, [load]);
  window.spike = { scene, ready: phase === 'ready' || phase === 'empty', revision, renderer };
  const select = useCallback((id: string) => { scene.select(id); setRevision(r => r + 1); }, [scene]);
  const move = (x: number, y: number, factor = 1) => {
    scene.setViewport({ x: scene.viewport.x + x, y: scene.viewport.y + y, zoom: Math.min(2, Math.max(0.1, scene.viewport.zoom * factor)) });
    setRevision(r => r + 1);
  };
  const reveal = (selected: boolean) => {
    const node = selected ? scene.selected : scene.nodes[0];
    if (!node) return;
    scene.setViewport({ x: 24 - node.x * scene.viewport.zoom, y: 24 - node.y * scene.viewport.zoom, zoom: scene.viewport.zoom });
    setRevision(r => r + 1);
  };
  return <div className="workspace">
    <header><a className="brand" href="/">AMPHORA<span>research studio</span></a><div className="mode">Monitor</div><span className="fixture">Synthetic interaction prototype</span></header>
    <main>
      <div className="context"><div><p className="eyebrow">Campaign / population search</p><h1>Explore the execution</h1></div><p>Read-only · 10,000 logical nodes</p></div>
      <form className="toolbar" onSubmit={event => { event.preventDefault(); void load(query, 0); }}>
        <label htmlFor="search">Find a node</label><input id="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Name or number" maxLength={120} />
        <button type="submit">Search</button><button type="button" onClick={() => { setQuery(''); void load('', 0); }}>Reset</button>
        <label htmlFor="renderer">Prototype renderer</label><select id="renderer" value={renderer} onChange={event => setRenderer(event.target.value)}><option value="reactflow">React Flow</option><option value="cytoscape">Cytoscape</option></select>
      </form>
      <div className="status" role="status">{phase === 'loading' ? 'Loading graph…' : phase === 'failed' ? 'Graph unavailable. Retry with Search.' : `${scene.nodes.length.toLocaleString()} shown · ${scene.omitted.toLocaleString()} outside this window · ${scene.total.toLocaleString()} matching nodes`}</div>
      <div className="work-area">
        <section className="graph-region" aria-label="Graph workspace" aria-busy={phase === 'loading'}>
          {phase === 'empty' ? <div className="empty"><h2>No matching nodes</h2><p>Try a different name or reset your search.</p></div> : renderer === 'reactflow' ? <FlowCanvas scene={scene} revision={revision} select={select} /> : <CyCanvas scene={scene} revision={revision} select={select} />}
          <div className="graph-controls" aria-label="Graph navigation"><button onClick={() => move(100,0)} aria-label="Pan left">←</button><button onClick={() => move(-100,0)} aria-label="Pan right">→</button><button onClick={() => move(0,100)} aria-label="Pan up">↑</button><button onClick={() => move(0,-100)} aria-label="Pan down">↓</button><button onClick={() => move(0,0,1.25)} aria-label="Zoom in">+</button><button onClick={() => move(0,0,0.8)} aria-label="Zoom out">−</button><button className="text-control" disabled={!scene.nodes.length} onClick={() => reveal(false)}>Show window</button></div>
        </section>
        <aside aria-label="Node navigator">
          <div className="inspector" aria-label="Selected node"><p className="eyebrow">Selected node</p>{scene.selected ? <><h2>{scene.selected.label}</h2><p className={`outcome ${scene.selected.status}`}>{scene.selected.status}</p><p>{scene.selectionOutsideWindow ? 'Selection retained outside this window.' : 'In the current window.'}</p><p className="muted">Synthetic status · no scientific result</p></> : <><h2>Follow a node</h2><p>Select on the graph or use the list below.</p></>}</div>
          <button className="reveal-selection" disabled={!scene.selected || scene.selectionOutsideWindow} onClick={() => reveal(true)}>Show selected node</button>
          <div className="list-heading"><h2>Nodes in this window</h2><span>{scene.nodes.length}</span></div>
          <ul className="node-list" aria-label="Searchable node list">{scene.nodes.map(node => <li key={node.id}><button data-node-id={node.id} aria-pressed={scene.selected?.id === node.id} onClick={() => select(node.id)}><span>{node.label}</span><small>{node.status}</small></button></li>)}</ul>
          <div className="pages"><button disabled={scene.offset === 0 || phase === 'loading'} onClick={() => void load(query, Math.max(0,scene.offset-200))}>Previous 200</button><button disabled={scene.offset+scene.nodes.length >= scene.total || phase === 'loading'} onClick={() => void load(query, scene.offset+200)}>Next 200</button></div>
        </aside>
      </div>
      <footer>Topology and states are synthetic. Layout changes are local; this prototype cannot change a running campaign.</footer>
    </main>
  </div>;
}
createRoot(document.getElementById('root')!).render(<Workspace />);
