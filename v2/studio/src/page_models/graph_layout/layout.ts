import ElkModule, { type ELK, type ElkNode } from 'elkjs/lib/elk.bundled.js';
import type { SceneNode, SceneEdge } from '../scene.js';

export const NODE_WIDTH = 208;
export const NODE_HEIGHT = 72;
export interface RoutedEdge extends SceneEdge { readonly path: string; readonly points: readonly Readonly<{ x: number; y: number }>[]; }
export interface GraphGeometry { readonly nodes: readonly SceneNode[]; readonly edges: readonly RoutedEdge[]; }

export function fitGeometry(geometry:GraphGeometry,width:number,height:number,ids?:readonly string[]) {
  const selected=ids?.length ? geometry.nodes.filter(n=>ids.includes(n.id)) : geometry.nodes;
  if(!selected.length || !Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)return null;
  const left=Math.min(...selected.map(n=>n.x)),top=Math.min(...selected.map(n=>n.y));
  const w=Math.max(...selected.map(n=>n.x+NODE_WIDTH))-left,h=Math.max(...selected.map(n=>n.y+NODE_HEIGHT))-top;
  const zoom=Math.max(.05,Math.min(1,width/(w*1.24),height/(h*1.24)));
  return {x:width/2-(left+w/2)*zoom,y:height/2-(top+h/2)*zoom,zoom};
}

/** Local geometry only. IDs and topology are immutable owner inputs. */
export async function layoutGraph(nodes: readonly SceneNode[], edges: readonly SceneEdge[]): Promise<GraphGeometry> {
  const ids = new Set(nodes.map(node => node.id));
  if (nodes.length > 200 || ids.size !== nodes.length || new Set(edges.map(e => e.id)).size !== edges.length ||
      edges.some(e => !ids.has(e.source) || !ids.has(e.target))) throw new Error('Invalid bounded graph');
  if (!nodes.length) return { nodes: [], edges: [] };
  const ordered = [...nodes].sort((a, b) => a.id.localeCompare(b.id));
  const aliases = new Map(ordered.map((node, index) => [node.id, 'node-' + index]));
  const orderedEdges = [...edges].sort((a, b) => a.id.localeCompare(b.id));
  // The upstream CommonJS bundle exposes a constructor; NodeNext sees its namespace.
  const Constructor = ElkModule as unknown as { new(): ELK };
  const elk = new Constructor();
  const result = await elk.layout<ElkNode>({ id: 'scene', layoutOptions: {
    'elk.algorithm': 'layered', 'elk.direction': 'DOWN', 'elk.edgeRouting': 'ORTHOGONAL',
    'elk.spacing.nodeNode': '44', 'elk.layered.spacing.nodeNodeBetweenLayers': '28',
    'elk.padding': '[top=24,left=24,bottom=24,right=24]', 'elk.randomSeed': '1',
  }, children: ordered.map(node => ({ id: aliases.get(node.id)!, width: NODE_WIDTH, height: NODE_HEIGHT,
    layoutOptions: { 'elk.portConstraints': 'FIXED_POS' }, ports: [
      { id: aliases.get(node.id)! + ':in', width: 0, height: 0, x: NODE_WIDTH / 2, y: 0,
        layoutOptions: { 'elk.port.side': 'NORTH' } },
      { id: aliases.get(node.id)! + ':out', width: 0, height: 0, x: NODE_WIDTH / 2, y: NODE_HEIGHT,
        layoutOptions: { 'elk.port.side': 'SOUTH' } },
    ] })), edges: orderedEdges.map((edge, index) => ({
      id: 'edge-' + index, sources: [aliases.get(edge.source)! + ':out'], targets: [aliases.get(edge.target)! + ':in'],
    })) });
  const positions = new Map(result.children?.map(node => [node.id, node]));
  const routes = new Map(result.edges?.map(edge => [orderedEdges[Number(edge.id.slice(5))]!.id, edge]));
  return { nodes: nodes.map(node => {
    const position = positions.get(aliases.get(node.id)!);
    if (!Number.isFinite(position?.x) || !Number.isFinite(position?.y)) throw new Error('Layout unavailable');
    return { ...node, x: position!.x!, y: position!.y! };
  }), edges: edges.map(edge => {
    const section = routes.get(edge.id)?.sections?.[0];
    if (!section) throw new Error('Edge route unavailable');
    const points = [section.startPoint, ...(section.bendPoints ?? []), section.endPoint];
    return { ...edge, points, path: points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ') };
  }) };
}
