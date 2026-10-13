import {useCallback,useEffect,useMemo,useState,useSyncExternalStore} from 'react';
import type {RunContext} from '../../page_models/graph_window.js';
import {CandidateDiscoveryModel} from '../../page_models/candidate_inspector/discovery.js';
import {ObservationClient} from '../../transport/observations.js';
import {CandidateInspector} from './panel.js';

export function CandidateResults({context,inspectExecution}:{context:RunContext;inspectExecution?:(activation:string)=>void}){
 const model=useMemo(()=>new CandidateDiscoveryModel(context,new ObservationClient()),[context.scope.tenant_id,context.scope.project_id,context.run]);
 const listen=useCallback((notify:()=>void)=>model.subscribe(notify),[model]),view=useSyncExternalStore(listen,()=>model.snapshot);
 const [selected,setSelected]=useState<string|null>(null),[visible,setVisible]=useState(()=>document.visibilityState==='visible');
 useEffect(()=>{const changed=()=>{const shown=document.visibilityState==='visible';setVisible(shown);setSelected(null);if(shown)void model.refresh();else model.clear();};document.addEventListener('visibilitychange',changed);changed();return()=>{document.removeEventListener('visibilitychange',changed);model.dispose();};},[model]);
 const discovery=view.discovery,choice=discovery?.choices.find(c=>c.key===selected);
 return <section className="candidate-results" aria-label="Candidate structures"><header><div><p className="eyebrow">Campaign outputs</p><h2>Candidate structures</h2></div><button disabled={view.phase==='loading'||!visible} onClick={()=>{setSelected(null);void model.refresh();}}>Refresh candidate outputs</button></header>
  {view.phase==='loading'&&<p role="status">Looking for retained chemical structures…</p>}{view.message&&<p role="status">{view.message}</p>}
  {discovery&&<><p>{discovery.scanned} of {discovery.total} execution steps inspected. {discovery.incomplete?'Partial discovery: more nodes or collection outputs may contain structures.':'All direct outputs in this snapshot were inspected.'}</p>
   {discovery.choices.length?<><label>Structure-producing step<select value={selected??''} onChange={event=>setSelected(event.target.value||null)}><option value="">Choose a retained structure</option>{discovery.choices.map(c=><option key={c.key} value={c.key}>{c.label}</option>)}</select></label><p>These are supplied structures, not ranked recommendations.</p></>:<p>No supported chemical structure output was found. Scalar screening parameters cannot determine a molecule.</p>}
  </>}
  {visible&&choice&&discovery&&<CandidateInspector key={choice.key} anchor={discovery.anchor} detail={choice.detail} {...(inspectExecution?{inspectExecution:()=>inspectExecution(choice.key)}:{})}/>} 
 </section>;
}
