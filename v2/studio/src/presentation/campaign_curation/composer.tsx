import { useCallback,useEffect,useState,useSyncExternalStore } from 'react';
import type { CurationRequestModel } from '../../page_models/campaign_curation/request.js';
import type { CurationPreparation } from '../../page_models/campaign_curation/preparation.js';
import type { CurationSelection } from '../../transport/campaign_curation/identity.js';
import './style.css';

export function CurationComposer({request,preparation,review,synthetic}:{request:CurationRequestModel;preparation:CurationPreparation;
  review:(selection:CurationSelection)=>void;synthetic:boolean}){
  const [direction,setDirection]=useState('');
  const listen=useCallback((notify:()=>void)=>request.subscribe(notify),[request]);
  const listenPreparation=useCallback((notify:()=>void)=>preparation.subscribe(notify),[preparation]);
  const view=useSyncExternalStore(listen,()=>request.snapshot),context=useSyncExternalStore(listenPreparation,()=>preparation.snapshot);
  useEffect(()=>{
    let stopped=false;
    const resume=async()=>{
      if(stopped||document.hidden)return;
      await request.initialize();if(stopped||document.hidden)return;
      if(request.canReconcile)await request.reconcile();
      if(!stopped&&!document.hidden&&request.canSubmit)await preparation.load();
    };
    const visibility=()=>{if(document.hidden){request.suspend();preparation.clear();}else void resume();};
    void resume();document.addEventListener('visibilitychange',visibility);
    return()=>{stopped=true;document.removeEventListener('visibilitychange',visibility);request.suspend();preparation.clear();};
  },[request,preparation]);
  const busy=['restoring','preparing','submitting','reconciling'].includes(view.phase);
  const message=view.phase==='accepted'?'Revision request recorded. The model result is read separately.':
    view.phase==='storage_failed'?'The browser recovery record is unavailable. Reopen this workspace before submitting.':
    view.phase==='denied'?'Revision access is unavailable to this session. Reopen the workspace.':
    view.phase==='conflict'?'This request conflicts with an existing record. The original has been preserved.':
    view.phase==='unresolved'?'Confirmation is unavailable. Check the original request before trying again.':
    busy?'Preparing or checking the original revision request...':
    context.phase==='running'?'This campaign is still active. Prepare its revision after execution finishes.':
    context.phase==='denied'?'The original campaign context is not available to this session.':
    context.phase==='failed'?context.reason==='curation_knowledge_unavailable'?'The retained Knowledge selection is unavailable. It has not been dropped from the request.':
      'The exact original campaign context could not be prepared. No revision was submitted.':
    context.phase==='loading'?'Reading the original campaign and its selected context...':
    view.reason==='invalid_request'?'Check the revision direction and selected context.':null;
  const prepared=context.prepared;
  return <section className="curation-composer" aria-label="Request a campaign revision">
    <h2>Ask for the next campaign</h2><p>Describe what should change. The model can propose a revised graph or identify tools that still need to be supplied.</p>
    {synthetic&&<p className="curation-synthetic">Synthetic engineering context · not a scientific validation</p>}
    {message&&<p role="status">{message}</p>}
    {request.canSubmit&&<form onSubmit={event=>{event.preventDefault();if(prepared&&direction.trim())void request.submit(prepared.request(direction,crypto.randomUUID()));}}>
      <label>What should the next campaign investigate?<textarea rows={4} maxLength={4096} required value={direction} onChange={event=>setDirection(event.target.value)}/></label>
      {prepared&&<p className="curation-context-summary">Original campaign definition · {prepared.context.knowledge.length} Knowledge revisions · {prepared.context.questions.length} research questions · {prepared.context.needs.length} evidence needs</p>}
      <div className="curation-compose-actions"><button className="primary" disabled={!prepared||!direction.trim()||busy}>Request graph revision</button>
        <button type="button" disabled={context.phase==='loading'} onClick={()=>void preparation.load()}>Refresh campaign context</button></div>
      <p className="curation-context-summary">This requests a proposal for a future campaign. It does not change the original run or launch the proposed graph.</p>
    </form>}
    {view.phase==='unresolved'&&<div className="curation-compose-actions"><button onClick={()=>void request.reconcile()}>Check original request</button>
      <button onClick={()=>void request.retryOriginal()}>Retry same request</button></div>}
    {view.phase==='accepted'&&request.submission&&<button onClick={()=>review(request.submission!.selection)}>Review model proposal</button>}
  </section>;
}
