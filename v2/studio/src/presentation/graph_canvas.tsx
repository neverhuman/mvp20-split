import { memo, useRef } from 'react';
import { ReactFlow, Background, Handle, Position, type NodeProps, type Node, type ReactFlowInstance } from '@xyflow/react';
import type { SceneNode, SceneEdge, Viewport } from '../page_models/scene.js';
import '@xyflow/react/dist/style.css';

const TaskNode = memo(({ data }: NodeProps<Node<{ label: string; status: string }>>) => <>
  <Handle type="target" position={Position.Left} isConnectable={false} />
  <span className="node-status">{data.status}</span><strong>{data.label}</strong>
  <Handle type="source" position={Position.Right} isConnectable={false} />
</>);
const types = { task: TaskNode };
type Props = { nodes: readonly SceneNode[]; edges?: readonly SceneEdge[]; selection: string | null; select: (id: string) => void;
  initialViewport?: Viewport; rememberViewport?: (viewport: Viewport) => void };

/** Presentation only; links must come from an owner-verified bounded topology projection. */
export function GraphCanvas({ nodes, edges = [], selection, select, initialViewport, rememberViewport }: Props) {
  const flow = useRef<Pick<ReactFlowInstance, 'setViewport' | 'getViewport'> | null>(null);
  const move = (x: number, y: number, scale = 1) => {
    if (!flow.current) return;
    const view = flow.current.getViewport();
    void flow.current.setViewport({ x: view.x+x, y: view.y+y, zoom: Math.min(2,Math.max(0.1,view.zoom*scale)) });
  };
  const reveal = () => {
    const node = nodes.find(n => n.id === selection) ?? nodes[0];
    if (!node || !flow.current) return;
    const { zoom } = flow.current.getViewport();
    void flow.current.setViewport({ x: 24-node.x*zoom, y: 24-node.y*zoom, zoom });
  };
  return <section className="graph-region" aria-label="Activation workspace">
    <ReactFlow nodes={nodes.map(n => ({ id: n.id, type: 'task', position: { x: n.x, y: n.y }, data: { label: n.label, status: n.status },
      selected: n.id === selection, ariaLabel: `${n.label}, ${n.status}`, className: `task-node ${n.status}` }))}
      edges={edges.map(edge => ({ ...edge }))} nodeTypes={types} onInit={instance => { flow.current = instance; }}
      onNodeClick={(_, node) => select(node.id)} onNodesChange={changes => { for (const change of changes) if (change.type === 'select' && change.selected) select(change.id); }}
      defaultViewport={initialViewport ?? { x: 24, y: 24, zoom: 0.85 }} onMoveEnd={(_, viewport) => rememberViewport?.(viewport)}
      minZoom={0.1} maxZoom={2} nodesDraggable={false} nodesConnectable={false}
      edgesFocusable={false} deleteKeyCode={null} autoPanOnNodeFocus={false} zoomOnDoubleClick={false}>
      <Background gap={24} color="#d8dfdf" />
    </ReactFlow>
    <div className="graph-controls" aria-label="Graph navigation">
      <button onClick={() => move(100,0)} aria-label="Pan left">←</button><button onClick={() => move(-100,0)} aria-label="Pan right">→</button>
      <button onClick={() => move(0,100)} aria-label="Pan up">↑</button><button onClick={() => move(0,-100)} aria-label="Pan down">↓</button>
      <button onClick={() => move(0,0,1.25)} aria-label="Zoom in">+</button><button onClick={() => move(0,0,0.8)} aria-label="Zoom out">−</button>
      <button className="text-control" onClick={reveal} disabled={!nodes.length}>Show selection</button>
    </div>
  </section>;
}
