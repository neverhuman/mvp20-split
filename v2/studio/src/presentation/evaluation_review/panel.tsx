import {useEffect,useMemo,useRef,useState} from 'react';
import {EvaluationReview,concerns,type Concern,type ReviewStep} from '../../page_models/evaluation_review/model.js';
import {polymerProposal} from '../../page_models/evaluation_review/polymer_proposal.js';
import {GraphCanvas} from '../graph_canvas.js';
import './style.css';

function download(raw:string,name:string){const url=URL.createObjectURL(new Blob([raw],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const label=(value:string)=>value.replaceAll('_',' ');
function Inspector({node,review,changed}:{node:ReviewStep;review:EvaluationReview;changed:()=>void}){
  const [concern,setConcern]=useState<Concern>('unsupported_assumption'),[change,setChange]=useState(''),[message,setMessage]=useState('');
  const fields:[string,string|readonly string[]][]=[['Why this step?',node.rationale],['Proposed method',node.method],['Evaluation procedure',node.procedure],['Inputs needed',node.inputs],['Expected outputs',node.outputs],['Applicability',node.applicability],['Assumptions to challenge',node.assumptions],['Decision rule',node.rule],['Evidence available',node.evidence],['Implementation status',node.availability],['Alternatives',node.alternatives],['Reference sources',node.sources]];
  return <aside className="evaluation-inspector" aria-label="Evaluation step inspector"><p className="eyebrow">{node.kind} / Design proposal</p><h2>{node.title}</h2>
    <form onSubmit={e=>{e.preventDefault();try{review.save(node.id,concern,change);changed();setMessage('Saved locally for a future campaign. Export to keep it.');setChange('');}catch(error){setMessage(String(error));}}}>
      <h3>Challenge this step</h3><label>Concern<select aria-label="Concern" value={concern} onChange={e=>setConcern(e.target.value as Concern)}>{concerns.map(c=><option key={c} value={c}>{label(c)}</option>)}</select></label>
      <label>What should change next campaign?<textarea required maxLength={2048} rows={3} value={change} onChange={e=>setChange(e.target.value)} /></label>
      <button type="submit">Save concern</button><p role="status">{message}</p>
    </form>
    <dl>{fields.map(([title,value])=><div key={title}><dt>{title}</dt><dd>{typeof value==='string'?value:value.length?<ol>{value.map((s,i)=><li key={i}>{s}</li>)}</ol>:'None specified'}</dd></div>)}</dl>
  </aside>;
}
/** A distinct local design review, never a relabelled execution view. */
export function EvaluationReviewPanel({synthetic}:{synthetic:boolean}){
  const [review,setReview]=useState<EvaluationReview|null>(()=>synthetic?new EvaluationReview(polymerProposal()):null);
  const [selected,setSelected]=useState('solvency'),[revision,setRevision]=useState(0),[message,setMessage]=useState('');
  const [pending,setPending]=useState<EvaluationReview|null>(null),generation=useRef(0);
  const scene=useMemo(()=>review?.scene(),[review]),node=review?.design.nodes.find(n=>n.id===selected)??review?.design.nodes[0];
  const notes=review?.feedback??[];
  useEffect(()=>{const handler=(e:BeforeUnloadEvent)=>{if(notes.length){e.preventDefault();e.returnValue='';}};window.addEventListener('beforeunload',handler);return()=>window.removeEventListener('beforeunload',handler);},[review,revision]);
  useEffect(()=>()=>{generation.current++;},[]);
  const adopt=(next:EvaluationReview)=>{setReview(next);setSelected(next.design.nodes.find(n=>n.kind==='objective')!.id);setPending(null);setRevision(n=>n+1);setMessage('Imported local review. It has not been submitted to an owner service.');};
  return <main className="evaluation-review">
    <header><p className="eyebrow">Evaluation design / SME review</p><h1>{review?.design.title??'Inspect an evaluation design'}</h1>
      <p className="evaluation-boundary"><strong>Unexecuted design proposal.</strong> Separate from the numerical campaign. Review the criteria and methods, then export corrections for a future campaign.</p>
      {review&&<details><summary>Authorship and scope</summary><p>{review.design.provenance.description}</p><p>Declared author: {review.design.provenance.author}. Revision {review.design.revision}. Imported authorship is not authenticated.</p></details>}
      <div className="evaluation-actions"><label>Import design or saved review<input type="file" accept="application/json,.json" onChange={async e=>{const file=e.target.files?.[0];e.target.value='';if(!file)return;const ticket=++generation.current;try{if(file.size>524288)throw Error('File exceeds 512 KiB');const text=await file.text();if(ticket!==generation.current)return;const next=EvaluationReview.import(text);if(review)setPending(next);else adopt(next);}catch(error){if(ticket===generation.current)setMessage(`Import rejected: ${String(error)}`);}}} /></label>
        {review&&<button onClick={()=>{download(review.export(),`${review.design.id}-review.json`);setMessage('Downloaded local review. No campaign changed and no model was invoked.');}}>Export review ({notes.length})</button>}
      </div>
      {pending&&<div role="status"><p>Replace this local review? Export first to keep your current notes.</p><button onClick={()=>adopt(pending)}>Replace local review</button><button onClick={()=>setPending(null)}>Keep current review</button></div>}
      <p role="status">{message}</p>
    </header>
    {review&&scene&&node&&<><p className="evaluation-guide">Select a criterion or method to inspect its rationale, assumptions and decision rule. Side-by-side methods are proposed independent evaluations, not observed concurrent executions.</p>
      <div className="evaluation-layout"><div className="evaluation-canvas"><GraphCanvas key={JSON.stringify(review.design)} {...scene} label="Evaluation design graph" selection={node.id} select={setSelected} minimap />
        <nav aria-label="Evaluation steps">{review.design.nodes.map(n=><button key={n.id} aria-pressed={n.id===node.id} onClick={()=>setSelected(n.id)}>{n.title}</button>)}</nav>
        <details><summary>What the connections mean</summary><ul>{review.design.edges.map((e,i)=><li key={i}>{review.design.nodes.find(n=>n.id===e.source)!.title} → {e.relationship} → {review.design.nodes.find(n=>n.id===e.target)!.title}</li>)}</ul></details>
      </div><Inspector key={node.id+JSON.stringify(review.design)} node={node} review={review} changed={()=>setRevision(n=>n+1)} /></div>
      <section aria-label="Next campaign review notes" className="evaluation-notes"><h2>Next campaign: {notes.length} concerns</h2><p>Local and unsubmitted. Export before closing or reloading. These notes do not alter the running campaign or automatically reach the LLM.</p>
        {!notes.length?<p>Flag a method, assumption, missing criterion or aggregation rule to begin.</p>:<ul>{notes.map(n=><li key={n.node+n.concern}><button onClick={()=>setSelected(n.node)}>{review.design.nodes.find(s=>s.id===n.node)!.title}</button><strong>{label(n.concern)}</strong><p>{n.change}</p><button onClick={()=>{review.remove(n.node,n.concern);setRevision(n=>n+1);}}>Remove concern</button></li>)}</ul>}
      </section></>}
  </main>;
}
