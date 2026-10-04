/** Presentation window only. Coordinates never change executable topology. */
export type SceneNode = Readonly<{ id: string; label: string; status: string; x: number; y: number }>;
export type SceneEdge = Readonly<{ id: string; source: string; target: string; label?: string }>;
export type ScenePage = Readonly<{ nodes: readonly SceneNode[]; edges: readonly SceneEdge[]; total: number; offset: number }>;
export type Viewport = Readonly<{ x: number; y: number; zoom: number }>;
export function checkedViewport(value: Viewport): Viewport {
  if (![value.x, value.y, value.zoom].every(Number.isFinite) || value.zoom < 0.1 || value.zoom > 2)
    throw new Error("Invalid viewport");
  return Object.freeze({ ...value });
}

export class SceneWindow {
  readonly limit = 200;
  nodes: readonly SceneNode[] = [];
  edges: readonly SceneEdge[] = [];
  total = 0;
  offset = 0;
  selected: SceneNode | null = null;
  viewport: Viewport = { x: 24, y: 24, zoom: 0.7 };

  replace(page: ScenePage): void {
    const ids = new Set(page.nodes.map(node => node.id));
    if (!Number.isSafeInteger(page.total) || !Number.isSafeInteger(page.offset)
      || page.offset < 0 || page.total < page.offset + page.nodes.length
      || page.nodes.length > this.limit || ids.size !== page.nodes.length
      || page.nodes.some(node => !node.id || !Number.isFinite(node.x) || !Number.isFinite(node.y))
      || new Set(page.edges.map(edge => edge.id)).size !== page.edges.length
      || page.edges.some(edge => !ids.has(edge.source) || !ids.has(edge.target))) {
      throw new Error("Invalid bounded scene");
    }
    // Copy/freeze to prevent a renderer from mutating the owner's projection.
    this.nodes = Object.freeze(page.nodes.map(node => Object.freeze({ ...node })));
    this.edges = Object.freeze(page.edges.map(edge => Object.freeze({ ...edge })));
    this.total = page.total;
    this.offset = page.offset;
    this.selected = this.nodes.find(node => node.id === this.selected?.id) ?? this.selected;
  }

  select(id: string): void {
    const node = this.nodes.find(value => value.id === id);
    if (!node) throw new Error("Selection must come from the visible scene");
    this.selected = node;
  }

  setViewport(value: Viewport): void {
    this.viewport = checkedViewport(value);
  }

  get omitted(): number { return this.total - this.nodes.length; }
  get selectionOutsideWindow(): boolean {
    return this.selected !== null && !this.nodes.some(node => node.id === this.selected!.id);
  }
}
