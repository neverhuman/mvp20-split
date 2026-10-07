import { decodeAuthoring } from '../../contracts/authoring.js';
import type { DraftPage } from '../../contracts/authoring.js';
import { AuthoringFailure } from '../../transport/authoring.js';
import type { AuthoringClient } from '../../transport/authoring.js';
import type { WorkspaceContext } from '../../transport/session/client.js';
import { same } from '../../transport/scientific/identity.js';
import { RequestLane } from '../request_lane.js';
import { DraftSession } from './draft_session.js';
import { DraftCommands } from './draft_commands.js';
import { EditorCatalog } from './editor_catalog.js';

type Source = Pick<AuthoringClient, 'drafts' | 'draft' | 'submit' | 'receipt' | 'validation' | 'universe' | 'releases' | 'schema'>;
type Phase = 'idle' | 'loading' | 'ready' | 'empty' | 'denied' | 'unavailable' | 'failed' | 'retained';
interface View { phase: Phase; page: DraftPage | null; selected: string | null; }
/** Scoped discovery owns loaded editing sessions; switching never discards unsaved work. */
export class DraftLibrary {
  private readonly lane = new RequestLane();
  private readonly listeners = new Set<() => void>();
  private readonly context: Pick<WorkspaceContext, 'actor_id' | 'scope'>;
  private disposed = false;
  private view: Readonly<View> = Object.freeze({phase:'idle',page:null,selected:null});
  private editor: { commands: DraftCommands; catalog: EditorCatalog } | null = null;
  constructor(context: Pick<WorkspaceContext, 'actor_id' | 'scope'>, private readonly source: Source) { this.context = structuredClone(context); }
  get snapshot() { return this.view; }
  get editing() { return this.editor; }
  subscribe(listener: () => void) { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; }
  private publish(value: Partial<View>) { if (!this.disposed) { this.view=Object.freeze({...this.view,...value}); for (const listener of this.listeners) listener(); } }
  private retained() {
    const editor=this.editor;
    if (!editor) return false;
    const state=editor.commands.session.snapshot;
    return state.dirty || !!state.pending || ['submitting','unresolved','reconciling'].includes(editor.commands.activation.snapshot.phase);
  }
  async refresh(after?: string) {
    if (this.disposed || this.view.phase === 'denied') return;
    const request=this.lane.begin(); this.publish({phase:'loading'});
    if (!request.current() || this.disposed) return;
    try {
      const page=decodeAuthoring('page',await this.source.drafts(after,request.signal));
      if (!request.current() || this.disposed) return;
      if (!same(page.scope,this.context.scope) || new Set(page.drafts.map(row=>row.draft_id)).size !== page.drafts.length) throw new Error('invalid_page');
      this.publish({phase:page.drafts.length ? 'ready' : 'empty',page:structuredClone(page)});
    } catch (error) { if (request.current()) this.fail(error); }
  }
  async open(id: string) {
    if (this.disposed || this.view.phase === 'denied' || id === this.view.selected) return;
    if (this.retained()) { this.publish({phase:'retained'}); return; }
    const head=this.view.page?.drafts.find(row=>row.draft_id === id);
    if (!head) throw new Error('draft_not_in_loaded_page');
    const request=this.lane.begin(); this.publish({phase:'loading'});
    if (!request.current() || this.disposed) return;
    try {
      const record=decodeAuthoring('draft',await this.source.draft(id,head.revision,request.signal));
      if (!request.current() || this.disposed) return;
      if (!same(record.scope,this.context.scope) || !same(record.head,head)) throw new Error('invalid_draft');
      // Work can become dirty while the read was pending. Never replace it silently.
      if (this.retained()) { this.publish({phase:'retained'}); return; }
      const session=new DraftSession(this.context.actor_id,this.context.scope,id,{title:record.head.title,definition:record.definition},record);
      this.closeEditor();
      this.editor={commands:new DraftCommands(session,this.source),catalog:new EditorCatalog(this.context.scope,this.source)};
      this.publish({phase:'ready',selected:id});
    } catch (error) { if (request.current()) this.fail(error); }
  }
  private fail(error: unknown) {
    const phase=error instanceof AuthoringFailure && error.kind === 'denied' ? 'denied' : error instanceof AuthoringFailure && error.kind === 'unavailable' ? 'unavailable' : 'failed';
    if (phase === 'denied') { this.editor?.commands.deny(); this.editor?.catalog.deny(); }
    this.publish({phase,...(phase === 'denied' ? {page:null} : {})});
  }
  private closeEditor() { this.editor?.commands.dispose(); this.editor?.catalog.dispose(); this.editor=null; }
  dispose() { this.disposed=true; this.lane.cancel(); this.closeEditor(); this.listeners.clear(); }
}
