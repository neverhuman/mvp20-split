import { memo, useEffect, useRef, useState } from 'react';
import { ReactFlow, Background, Handle, Position, MarkerType, BaseEdge, useNodesInitialized, useReactFlow,
  type EdgeProps, type NodeProps, type Node, type ReactFlowInstance } from '@xyflow/react';
import type { SceneNode, SceneEdge, Viewport } from '../page_models/scene.js';
import { layoutGraph, NODE_WIDTH, NODE_HEIGHT, type GraphGeometry } from '../page_models/graph_layout/layout.js';
import '@xyflow/react/dist/style.css';

const TaskNode = memo(({ data }: NodeProps<Node<{ label: string; status: string; annotation?: string }>>) => <>
  <Handle type="target" position={Position.Top} isConnectable={false} />
  <span className="node-status">{data.status}</span><strong title={data.label}>{data.label}</strong>
  {data.annotation && <span className="node-annotation">{data.annotation}</span>}
  <Handle type="source" position={Position.Bottom} isConnectable={false} />
</>);
const RoutedConnection = ({ id, data, markerEnd, style }: EdgeProps) =>
  <BaseEdge id={id} path={String(data?.path ?? '')} {...(markerEnd ? { markerEnd } : {})} {...(style ? { style } : {})} />;
const types = { task: TaskNode }, edgeTypes = { routed: RoutedConnection };
const EMPTY_EDGES: readonly SceneEdge[] = [];
type Props = { nodes: readonly SceneNode[]; edges?: readonly SceneEdge[]; selection: string | null; select: (id: string) => void;
  initialViewport?: Viewport | undefined; rememberViewport?: (viewport: Viewport) => void; label?: string; annotations?: Readonly<Record<string, string>> };

function InitialViewport({ geometryKey, viewport }: { geometryKey: string; viewport?: Viewport | undefined }) {
  const initialized = useNodesInitialized(), flow = useReactFlow(), applied = useRef<string | null>(null);
  useEffect(() => {
    if (!initialized || applied.current === geometryKey) return;
    applied.current = geometryKey;
    if (viewport) void flow.setViewport(viewport);
    else void flow.fitView({ padding: 0.12, minZoom: 0.05, maxZoom: 1 });
  }, [initialized, geometryKey, flow, viewport]);
  return null;
}

/** Renders real links with local routed geometry; never invents execution connections. */
export function GraphCanvas({ nodes, edges = EMPTY_EDGES, selection, select, initialViewport, rememberViewport,
  label = 'Activation workspace', annotations = {} }: Props) {
  const flow = useRef<Pick<ReactFlowInstance, 'setViewport' | 'getViewport' | 'fitView'> | null>(null);
  const key = JSON.stringify([nodes.map(n => n.id).sort(), edges.map(e => [e.id, e.source, e.target]).sort()]);
  const [layout, setLayout] = useState<{ key: string; geometry?: GraphGeometry; failed?: boolean } | null>(null);
  useEffect(() => {
    let active = true;
    void layoutGraph(nodes, edges).then(geometry => { if (active) setLayout({ key, geometry }); },
      () => { if (active) setLayout({ key, failed: true }); });
    return () => { active = false; };
  }, [key]);
  const geometry = layout?.key === key ? layout.geometry : undefined;
  const current = new Map(nodes.map(node => [node.id, node]));
  const move = (x: number, y: number, scale = 1) => {
    if (!flow.current) return;
    const view = flow.current.getViewport();
    void flow.current.setViewport({ x: view.x+x, y: view.y+y, zoom: Math.min(2,Math.max(0.05,view.zoom*scale)) });
  };
  const reveal = () => {
    const node = geometry?.nodes.find(n => n.id === selection) ?? geometry?.nodes[0];
    if (node && flow.current) void flow.current.fitView({ nodes: [{ id: node.id }], padding: 0.5, maxZoom: 1 });
  };
  return <section className="graph-region" aria-label={label} aria-busy={!geometry && !layout?.failed}>
    {!geometry && <p className="graph-message" role="status">{layout?.key === key && layout.failed ? 'Graph layout unavailable. Use the node list to inspect this scope.' : 'Arranging campaign connections...'}</p>}
    {geometry && !nodes.length && <p className="graph-message" role="status">No nodes loaded in this graph scope.</p>}
    <ReactFlow<Node> nodes={(geometry?.nodes ?? []).map(n => ({ id: n.id, type: 'task', position: { x: n.x, y: n.y },
      style: { width: NODE_WIDTH, height: NODE_HEIGHT }, data: { label: current.get(n.id)!.label, status: current.get(n.id)!.status,
        ...(annotations[n.id] ? { annotation: annotations[n.id] } : {}) }, selected: n.id === selection,
      ariaLabel: `${current.get(n.id)!.label}, ${current.get(n.id)!.status}${annotations[n.id] ? ', ' + annotations[n.id] : ''}`,
      className: `task-node ${current.get(n.id)!.status}` }))}
      edges={(geometry?.edges ?? []).map(edge => ({ id: edge.id, source: edge.source, target: edge.target, type: 'routed',
        data: { path: edge.path }, markerEnd: { type: MarkerType.ArrowClosed, color: '#42645d', width: 18, height: 18 },
        style: { stroke: selection === edge.source || selection === edge.target ? '#12695e' : '#647b75',
          strokeWidth: selection === edge.source || selection === edge.target ? 3 : 1.8,
          opacity: selection && selection !== edge.source && selection !== edge.target ? 0.35 : 1 } }))}
      nodeTypes={types} edgeTypes={edgeTypes} onInit={instance => { flow.current = instance; }}
      onNodeClick={(_, node) => select(node.id)} onNodesChange={changes => { for (const change of changes) if (change.type === 'select' && change.selected) select(change.id); }}
      defaultViewport={initialViewport ?? { x: 0, y: 0, zoom: 1 }} onMoveEnd={(_, viewport) => rememberViewport?.(viewport)}
      fitView={!initialViewport} fitViewOptions={{ padding: 0.12, minZoom: 0.05, maxZoom: 1 }}
      minZoom={0.05} maxZoom={2} nodesDraggable={false} nodesConnectable={false}
      edgesFocusable={false} deleteKeyCode={null} autoPanOnNodeFocus={false} zoomOnDoubleClick={false}>
      <Background gap={24} color="#d8dfdf" />
      {geometry && <InitialViewport geometryKey={key} viewport={initialViewport} />}
    </ReactFlow>
    <div className="graph-controls" aria-label="Graph navigation">
      <button onClick={() => move(100,0)} aria-label="Pan left">&#8592;</button><button onClick={() => move(-100,0)} aria-label="Pan right">&#8594;</button>
      <button onClick={() => move(0,100)} aria-label="Pan up">&#8593;</button><button onClick={() => move(0,-100)} aria-label="Pan down">&#8595;</button>
      <button onClick={() => move(0,0,1.25)} aria-label="Zoom in">+</button><button onClick={() => move(0,0,0.8)} aria-label="Zoom out">&#8722;</button>
      <button className="text-control" onClick={() => void flow.current?.fitView({ padding: 0.12, minZoom: 0.05, maxZoom: 1 })} disabled={!nodes.length}>Fit graph</button>
      <button className="text-control" onClick={reveal} disabled={!nodes.length}>Show selection</button>
    </div>
  </section>;
}
