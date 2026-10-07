import { SessionFailure } from '../../transport/session/client.js';
import type { SessionSource, WorkspaceContext } from '../../transport/session/client.js';

export interface SessionView { readonly phase: 'loading' | 'ready' | 'denied' | 'failed'; readonly context: WorkspaceContext | null; }
export class WorkspaceSession {
  private view: SessionView = { phase: 'loading', context: null };
  private generation = 0;
  private listeners = new Set<() => void>();
  constructor(private readonly source: SessionSource) {}
  get snapshot() { return this.view; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private publish(value: SessionView) { this.view = Object.freeze(value); for (const listener of this.listeners) listener(); }
  async open(ticket?: string) {
    const generation = ++this.generation;
    this.publish({ phase:'loading', context:null });
    try {
      const context = await this.source.open(ticket);
      if (generation === this.generation) this.publish({ phase:'ready', context });
    } catch (error) {
      if (generation === this.generation) this.publish({ phase:error instanceof SessionFailure && error.kind === 'denied' ? 'denied' : 'failed', context:null });
    }
  }
  dispose() { ++this.generation; this.listeners.clear(); }
}
