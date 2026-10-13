import {useCallback,useEffect,useState,useSyncExternalStore} from 'react';
import type {RetainedSelection} from '../../page_models/candidate_evidence/selection.js';
import type {GenerationModel} from '../../page_models/generation_comparison/model.js';
import type {RetainedGeneration} from '../../page_models/generation_comparison/checkpoint.js';
import './style.css';
const number=(n:number|null)=>n===null?'Unknown':new Intl.NumberFormat(undefined,{maximumSignificantDigits:6}).format(n);
function Checkpoint({value,label,selection}:{value:RetainedGeneration;label:string;selection:RetainedSelection}){
 const [page,setPage]=useState(0),rows=value.candidates.slice(page*20,(page+1)*20);
 return <section className="generation-record" aria-label={label+' checkpoint'}><h3>{label}: Generation {value.record.generation}</h3>
  <p>{value.record.phase.replaceAll('_',' ')} · {value.record.population.length} retained · {value.evaluated} evaluated · {value.unresolved} unresolved</p>
  <p>Recorded evidence labels: {[...new Set(value.candidates.map(c=>c.quality).filter(Boolean))].join(', ')||'none'}. These labels do not establish scientific validity.</p>
  <details><summary>Selection policy and trade-offs</summary><p>Configured policy: {selection.configuredPolicy}. Retained selection: {selection.policy??'No receipt'}.</p><p>{selection.disposition?.replaceAll('_',' ')??'Selection evidence unavailable'} ? {selection.selected.length} selected of {selection.requested??'unknown'} requested.</p><p>Objectives: {selection.objectives.map(o=>`${o.objective_id}: ${o.direction} (${o.unit})`).join('; ')}. No aggregate score is inferred.</p><p>Evaluator: {selection.evaluator.tool.capability_id} / {selection.evaluator.tool.release}.</p><p>Constraint artifact: {selection.evaluator.constraints.artifact_id}. Context artifacts: {selection.evaluator.context.length}.</p><p>These numerical search selections do not rank molecular structures.</p></details>
  <details><summary>Inspect candidates and ancestry ({value.candidates.length})</summary>
   <p>Numerical search vectors; no molecular structure is implied. Attempt history and retained population are distinct.</p>
   <ul>{rows.map(c=><li key={c.id}><strong>{c.retained?'Retained':'Attempt'} · {c.status}</strong><p>Genes: {c.genes.map(number).join(', ')}. Born in generation {c.generation}.</p>
    <p>Selection: {selection.forCandidate(c.id).state.replaceAll('_',' ')}{selection.forCandidate(c.id).front!==null?` ? recorded Pareto front ${selection.forCandidate(c.id).front}`:''}{selection.forCandidate(c.id).sameFront.length>1?` ? ${selection.forCandidate(c.id).sameFront.length} candidates on that front`:''}.</p><p>Constraint violation: {number(c.violation)}. Evidence: {c.quality??'unknown'}.</p>
    <p>{Object.entries(c.values).map(([name,v])=>name+': '+number(v)).join('; ')||'No objective values'}</p>
    <details><summary>Exact identity and parents</summary><code>{c.id}</code><p>{c.parents.length?c.parents.join(', '):'Seed; no parents'}</p></details></li>)}</ul>
   <button disabled={page===0} onClick={()=>setPage(p=>p-1)}>Previous candidates</button>{' '}
   <button disabled={(page+1)*20>=value.candidates.length} onClick={()=>setPage(p=>p+1)}>Next candidates</button>
   <p>Showing {page*20+1}–{Math.min((page+1)*20,value.candidates.length)} of {value.candidates.length} attempts.</p>
  </details>
  <details><summary>Retained checkpoint identity</summary><p>{value.reference.artifact_id}</p><code>{value.reference.sha256}</code><p>Declared specification: {value.record.specification_sha256}</p></details>
 </section>;
}
export function GenerationPanel({model,active=true}:{model:GenerationModel;active?:boolean}){
 const subscribe=useCallback((notify:()=>void)=>model.subscribe(notify),[model]);
 const view=useSyncExternalStore(subscribe,()=>model.snapshot);
 useEffect(()=>{if(active&&model.snapshot.phase==='idle')void model.refresh();},[model,active]);
 const comparison=model.comparison,choices=view.discovery?.choices??[];
 return <section className="generation-comparison" aria-label="Generation comparison"><header><h2>Compare retained generations</h2><button disabled={view.phase==='loading'} onClick={()=>void model.refresh()}>Refresh search outputs</button></header>
  <p>Inspect two recorded search checkpoints. Each objective keeps its own direction and units.</p>
  {view.message&&<p role="status">{view.message}</p>}
  {view.phase==='loading'&&<p role="status">Finding retained search outputs…</p>}
  {view.discovery&&<><p>{view.discovery.scanned} of {view.discovery.total} execution steps inspected. {view.discovery.incomplete?'Partial discovery: additional nodes or collection outputs may contain more checkpoints.':'All direct outputs in this observation were inspected.'}</p>
   {!choices.length?<p>No supported search checkpoints were found in this scan. A campaign of scientific screens does not automatically contain evolutionary generations.</p>:<>
    <div className="generation-selectors">{(['left','right'] as const).map((side,index)=><label key={side}>Checkpoint {index===0?'A':'B'}<select aria-label={'Checkpoint '+(index===0?'A':'B')} value={view[side].key??''} onChange={e=>void model.select(side,e.target.value)}><option value="">Choose a retained output</option>{choices.map((c,i)=><option key={c.key} value={c.key}>{i+1}. {c.locations[0]}</option>)}</select>{view[side].phase==='loading'&&<span role="status">Checking checkpoint…</span>}</label>)}</div>
    {comparison&&<><h3>Objective comparison</h3><p>{comparison.reason??'Same pinned search specification, different completed generations. Positive change means a better observed value from A to B.'}</p>
     <div className="generation-table"><table><caption>Best feasible retained value per objective; different objectives may refer to different candidates</caption><thead><tr><th>Objective</th><th>A</th><th>B</th><th>Change</th></tr></thead><tbody>{[...new Set([...comparison.left.objectives,...comparison.right.objectives].map(o=>o.id))].map(id=>{
      const a=comparison.left.objectives.find(o=>o.id===id),b=comparison.right.objectives.find(o=>o.id===id);
      return <tr key={id}><th>{id}</th><td>{number(a?.best??null)}<small>{a?`${a.unit} · ${a.direction} · ${a.count} feasible`: 'Not defined'}</small></td><td>{number(b?.best??null)}<small>{b?`${b.unit} · ${b.direction} · ${b.count} feasible`:'Not defined'}</small></td><td>{comparison.compatible?number(comparison.improvement(id)):'Not comparable'}</td></tr>;
     })}</tbody></table></div><p>This comparison does not prove direct ancestry, scientific validity or one overall winner.</p></>}
    <div className="generation-records">{view.left.value&&<Checkpoint key={'a'+view.left.key} label="A" value={view.left.value} selection={view.left.selection!}/>} {view.right.value&&<Checkpoint key={'b'+view.right.key} label="B" value={view.right.value} selection={view.right.selection!}/>}</div>
   </>}
  </>}
 </section>;
}
