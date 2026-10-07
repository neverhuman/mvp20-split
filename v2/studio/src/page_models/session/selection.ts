import { ExploreContext } from '../explore/context.js';
import type { ExplorePins } from '../explore/context.js';
import type { WorkspaceContext } from '../../transport/session/client.js';

/** A launcher link selects context; only the authenticated session grants scope. */
export class WorkspaceSelection {
  readonly phase: 'missing' | 'ready' | 'invalid';
  readonly pins: ExplorePins | null;
  constructor(search: string, scope: WorkspaceContext['scope']) {
    let pins: ExplorePins | null = null;
    let phase: WorkspaceSelection['phase'] = 'missing';
    try {
      if (search.length > 8192) throw new Error('selection_too_large');
      const values = new URLSearchParams(search).getAll('explore');
      if (values.length) {
        if (values.length !== 1) throw new Error('ambiguous_selection');
        const value = JSON.parse(values[0]!);
        if (!value || !Array.isArray(value.observations) || Object.keys(value).sort().join(',') !== 'experiment,graph,observations') throw new Error('invalid_selection');
        const context = new ExploreContext(value);
        context.scope(scope);
        pins = context.pins;
        phase = 'ready';
      }
    } catch { phase = 'invalid'; }
    this.phase = phase;
    this.pins = pins;
    Object.freeze(this);
  }
}
