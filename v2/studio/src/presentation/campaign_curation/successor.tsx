import {useCallback,useEffect,useState,useSyncExternalStore} from 'react';
import type {CurationGraphReview} from '../../page_models/campaign_curation/graph_review.js';
import type {SuccessorPreparation} from '../../page_models/successor_launch/preparation.js';
import type {SuccessorLaunchModel} from '../../page_models/successor_launch/model.js';
import type {SuccessorSubmission} from '../../transport/successor_launch/submission.js';
import type {SuccessorLaunchReceipt} from '../../contracts/successor_launch.js';

const phases={preparing:'Checking the proposed graph and installed tools',admission_unresolved:'Waiting for Runtime admission',rejected:'Runtime or Deployment rejected this launch',
  admitted_not_engaged:'New campaign admitted; workers are not engaged yet',engaging:'Starting the new campaign workers',engaged:'Workers engaged; open the new campaign to follow its steps',
  draining:'Campaign execution ended; releasing its workers',released:'Workers released; the new campaign remains available',recovery_required:'The original launch needs recovery'};

export function SuccessorPanel({review,preparation,launch,open}:{review:CurationGraphReview;preparation:SuccessorPreparation;launch:SuccessorLaunchModel;
  open:(command:SuccessorSubmission,receipt:SuccessorLaunchReceipt)=>void}){
  const listen=useCallback((notify:()=>void)=>launch.subscribe(notify),[launch]);
  const listenPreparation=useCallback((notify:()=>void)=>preparation.subscribe(notify),[preparation]);
  const view=useSyncExternalStore(listen,()=>launch.snapshot),ready=useSyncExternalStore(listenPreparation,()=>preparation.snapshot);
  const [profile,setProfile]=useState(''),[selections,setSelections]=useState<Record<string,number>>({});
  useEffect(()=>{
    let stopped=false;
    const tick=async()=>{
      if(stopped||document.hidden)return;launch.initialize();
      if(launch.canReconcile)await launch.reconcile();
      if(stopped||document.hidden)return;
      if(launch.canSubmit&&preparation.snapshot.phase==='idle')await preparation.load(review);
    };
    const visibility=()=>{if(document.hidden){launch.suspend();preparation.clear();}else void tick();};
    void tick();document.addEventListener('visibilitychange',visibility);
    return()=>{stopped=true;document.removeEventListener('visibilitychange',visibility);launch.suspend();preparation.clear();};
  },[review,preparation,launch]);
  useEffect(()=>{
    if(document.hidden||!launch.canReconcile||['released','rejected'].includes(view.receipt?.phase??''))return;
    const timer=setTimeout(()=>{if(!document.hidden&&launch.canReconcile)void launch.reconcile();},2000);
    return()=>clearTimeout(timer);
  },[launch,view.phase,view.receipt]);
  const prepared=ready.prepared,selectedProfile=profile||(prepared?.profiles.length===1?prepared.profiles[0]!.reference.profile_id:'');
  const mapped=prepared?.inputs.every(port=>Number.isSafeInteger(selections[port.name]))??false;
  const message=view.phase==='storage_failed'?'The launch recovery record is unavailable. No replacement request will be sent.':
    view.phase==='denied'?'Launch access is unavailable to this session.':view.phase==='conflict'?'This original launch conflicts with a retained request.':
    view.phase==='unresolved'?'Launch confirmation is unavailable. Check the original request or explicitly retry its same bytes.':
    ['submitting','reconciling','restoring'].includes(view.phase)?'Checking the original successor launch...':
    view.receipt?phases[view.receipt.phase]:ready.phase==='loading'?'Checking predecessor readiness and installed tools...':
    ready.phase==='denied'?'Predecessor or tool-profile access is denied.':ready.phase==='failed'?ready.reason==='successor_predecessor_changed'?
      'The predecessor changed after this proposal was requested. Prepare a new revision from its current state.':ready.reason==='successor_predecessor_unsettled'?
      'The predecessor is still settling. Refresh readiness after its work drains.':'Successor preparation could not be verified.':null;
  return <section className="curation-successor" aria-label="Launch reviewed successor"><h2>Run the revised campaign</h2>
    <p>The original campaign stays intact. Runtime checks the reviewed draft, predecessor and inputs again before admitting a new run.</p>
    {message&&<p role="status">{message}</p>}
    {launch.canSubmit&&<>
      {prepared&&<>
        {!prepared.profiles.length?<p>No installed profile supports every tool in this proposal. The graph remains available for review.</p>:
          <label>Installed tool profile<select value={selectedProfile} onChange={event=>setProfile(event.target.value)}><option value="">Choose a profile</option>
            {prepared.profiles.map(item=><option key={item.reference.profile_id} value={item.reference.profile_id}>{item.title}</option>)}</select></label>}
        {prepared.inputs.length>0&&<><h3>Carry results into the next campaign</h3><p>Choose a committed run export for each required input. Runtime checks types, units and retained values; matching names do not prove compatibility.</p>
          {prepared.inputs.map(port=><label key={port.name}>{port.name} ({port.description})<select value={selections[port.name]??''} onChange={event=>setSelections(previous=>{
            const next={...previous};if(event.target.value==='')delete next[port.name];else next[port.name]=Number(event.target.value);return next;})}>
            <option value="">Choose a retained result</option>{prepared.sources.sources.map((source,index)=><option key={index} value={index}>{source.source.port}</option>)}</select></label>)}
          {!prepared.sources.sources.length&&<p>No committed run exports are available. Node-local outputs and fresh manual inputs are not selectable in this view.</p>}</>}
      </>}
      <div className="curation-compose-actions"><button className="primary" disabled={!prepared||!selectedProfile||!mapped} onClick={()=>{
        if(prepared)void launch.submit(prepared.command(crypto.randomUUID(),selectedProfile,selections));}}>Run this revised campaign</button>
        <button disabled={ready.phase==='loading'} onClick={()=>{setSelections({});setProfile('');void preparation.load(review);}}>Refresh launch readiness</button></div>
    </>}
    {launch.canReconcile&&<div className="curation-compose-actions"><button onClick={()=>void launch.reconcile()}>Check original launch</button>
      {launch.canRetry&&<button onClick={()=>void launch.retryOriginal()}>Retry same launch request</button>}</div>}
    {view.receipt&&<p>{view.receipt.workers.ready} / {view.receipt.workers.expected} workers ready{view.receipt.reason_code?' · '+view.receipt.reason_code:''}</p>}
    {view.receipt?.run_id&&launch.submission&&<button className="primary" onClick={()=>open(launch.submission!,view.receipt!)}>Open new campaign</button>}
  </section>;
}
