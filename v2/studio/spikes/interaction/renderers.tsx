import { memo, useEffect, useRef } from 'react';
import { ReactFlow, Background, Handle, Position, type NodeProps, type Node, type ReactFlowInstance } from '@xyflow/react';
import cytoscape from 'cytoscape';
import type { SceneWindow } from '../../src/page_models/scene.js';
import '@xyflow/react/dist/style.css';

type Props = { scene: SceneWindow; revision: number; select: (id: string) => void };
const TaskNode = memo(({ data }: NodeProps<Node<{ label: string; status: string }>>) => <>
  <Handle type="target" position={Position.Left} isConnectable={false} />
  <span className="node-status">{data.status}</span><strong>{data.label}</strong>
  <Handle type="source" position={Position.Right} isConnectable={false} />
</>);
const nodeTypes = { task: TaskNode };

export function FlowCanvas({ scene, revision, select }: Props) {
  const flow = useRef<Pick<ReactFlowInstance, 'setViewport'> | null>(null);
  const nodes = scene.nodes.map(n => ({ id: n.id, type: 'task', position: { x: n.x, y: n.y },
    data: { label: n.label, status: n.status }, selected: scene.selected?.id === n.id,
    ariaLabel: `${n.label}, ${n.status}`, className: `task-node ${n.status}` }));
  useEffect(() => { if (flow.current) void flow.current.setViewport(scene.viewport); }, [revision, scene]);
  return <ReactFlow nodes={nodes} edges={scene.edges.map(e => ({ ...e }))} nodeTypes={nodeTypes}
    onInit={value => { flow.current = value; }} defaultViewport={scene.viewport}
    onNodeClick={(_, node) => select(node.id)}
    onNodesChange={changes => { for (const change of changes) if (change.type === 'select' && change.selected) select(change.id); }}
    onMoveEnd={(_, value) => scene.setViewport(value)} minZoom={0.1} maxZoom={2}
    nodesDraggable={false} nodesConnectable={false} edgesFocusable={false} deleteKeyCode={null}
    zoomOnDoubleClick={false} aria-label="Campaign graph" onlyRenderVisibleElements={false}>
    <Background gap={24} color="#d8dfdf" />
  </ReactFlow>;
}

export function CyCanvas({ scene, revision, select }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const cy = useRef<cytoscape.Core | null>(null);
  const callback = useRef(select); callback.current = select;
  useEffect(() => {
    if (!container.current) return;
    const core = cytoscape({ container: container.current, minZoom: 0.1, maxZoom: 2,
      autoungrabify: true, boxSelectionEnabled: false, layout: { name: 'preset' },
      style: [
        { selector: 'node', style: { shape: 'round-rectangle', width: 205, height: 68, 'background-color': '#ffffff', 'border-color': '#637e7b', 'border-width': 2,
          label: 'data(label)', 'font-size': 12, 'text-valign': 'center', 'text-wrap': 'wrap', 'text-max-width': '190px', color: '#1d3432' } },
        { selector: 'edge', style: { width: 1.5, 'line-color': '#839692', 'target-arrow-color': '#839692', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } },
        { selector: ':selected', style: { 'border-color': '#12695e', 'border-width': 4 } },
      ] });
    core.on('tap', 'node', event => callback.current(event.target.id()));
    core.on('pan zoom', () => scene.setViewport({ ...core.pan(), zoom: core.zoom() }));
    cy.current = core; return () => { core.destroy(); cy.current = null; };
  }, [scene]);
  useEffect(() => {
    const core = cy.current; if (!core) return;
    const viewport = { ...scene.viewport };
    core.batch(() => {
      core.elements().remove();
      core.add(scene.nodes.map(n => ({ group: 'nodes' as const, data: { id: n.id, label: `${n.status}\n${n.label.length > 52 ? n.label.slice(0, 51) + '…' : n.label}` }, position: { x: n.x+102, y: n.y+34 }, selected: scene.selected?.id === n.id })));
      core.add(scene.edges.map(e => ({ group: 'edges' as const, data: { ...e } })));
    });
    core.viewport({ zoom: viewport.zoom, pan: { x: viewport.x, y: viewport.y } });
  }, [scene, revision]);
  return <div ref={container} className="cy-canvas" role="img" aria-label="Campaign graph; use the searchable node list for keyboard navigation" />;
}
