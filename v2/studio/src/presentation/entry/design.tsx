import { useCallback, useEffect, useSyncExternalStore } from 'react';
import type { DraftLibrary } from '../../page_models/design/library.js';
import { DraftWorkspace } from '../draft_workspace.js';

export function LocalDesign({ model, synthetic }: { model: DraftLibrary; synthetic: boolean }) {
  const subscribe=useCallback((notify: () => void)=>model.subscribe(notify),[model]);
  const view=useSyncExternalStore(subscribe,()=>model.snapshot);
  useEffect(()=>{ void model.refresh(); },[model]);
  const editor=model.editing;
  return <>
    <section className="local-draft-library" aria-label="Saved campaign drafts">
      <h2>Next-campaign drafts</h2>
      <p>Changes belong to a future campaign. Select a saved draft to inspect or revise.</p>
      <div className="toolbar"><button disabled={view.phase === 'loading' || view.phase === 'denied'} onClick={()=>void model.refresh()}>Refresh drafts</button>
        {view.page?.next_after && <button disabled={view.phase === 'loading'} onClick={()=>void model.refresh(view.page!.next_after!)}>Next drafts</button>}
      </div>
      <p role="status">{view.phase === 'loading' ? 'Loading saved drafts.' : view.phase === 'empty' ? 'No saved drafts in this workspace.' : view.phase === 'denied' ? 'Draft access denied.' : view.phase === 'unavailable' ? 'Draft authoring is unavailable in this installation.' : view.phase === 'failed' ? 'Saved drafts could not be loaded.' : view.phase === 'retained' ? 'Finish saving or reconciling this draft before switching. Your local work is retained.' : ''}</p>
      {view.page && <ul className="local-draft-list">{view.page.drafts.map(head=><li key={head.draft_id}><button aria-pressed={view.selected === head.draft_id} disabled={view.phase === 'loading'} onClick={()=>void model.open(head.draft_id)}>{head.title} / revision {head.revision}</button></li>)}</ul>}
    </section>
    {editor && <DraftWorkspace commands={editor.commands} catalog={editor.catalog} synthetic={synthetic} />}
  </>;
}
