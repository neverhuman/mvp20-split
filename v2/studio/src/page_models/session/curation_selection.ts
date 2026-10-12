import type { WorkspaceContext } from '../../transport/session/client.js';
import { validSelection, type CurationSelection } from '../../transport/campaign_curation/identity.js';
import { immutable } from '../explore/context.js';

/** A selected original reference is navigation only; authenticated context supplies scope. */
export class WorkspaceCurationSelection {
  readonly phase: 'missing' | 'ready' | 'invalid';
  readonly selection: CurationSelection | null;
  constructor(search: string, context: WorkspaceContext & { run_id: string }) {
    let phase: WorkspaceCurationSelection['phase'] = 'missing', selection: CurationSelection | null = null;
    try {
      if (search.length > 16384) throw Error('selection_too_large');
      const values = new URLSearchParams(search).getAll('curation');
      if (values.length) {
        if (values.length !== 1) throw Error('ambiguous_selection');
        const candidate = { reference: { scope: context.scope, curation_id: values[0]! },
          actor: context.actor_id, predecessor: context.run_id };
        validSelection(candidate); selection = immutable(candidate); phase = 'ready';
      }
    } catch { phase = 'invalid'; }
    this.phase = phase; this.selection = selection; Object.freeze(this);
  }
}
