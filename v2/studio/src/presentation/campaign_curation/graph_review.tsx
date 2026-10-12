import {useCallback,useEffect,useState,useSyncExternalStore,type ReactNode} from 'react';
import type {CurationGraphReview} from '../../page_models/campaign_curation/graph_review.js';
import type {RecordedCuration} from '../../page_models/campaign_curation/records.js';
import type {CurationGraphModel} from '../../page_models/campaign_curation/graph_model.js';
import {curationGraphScene} from '../../page_models/campaign_curation/graph_scene.js';
import {GraphCanvas} from '../graph_canvas.js';

export function CurationGraphPanel({record,model,actions}:{record:RecordedCuration;model:CurationGraphModel;actions?:(review:CurationGraphReview)=>ReactNode}){
  const listen=useCallback((notify:()=>void)=>model.subscribe(notify),[model]);
  const view=useSyncExternalStore(listen,()=>model.snapshot);
  const [side,setSide]=useState<'original'|'proposed'>('proposed'),[path,setPath]=useState<string[]>([]),[offset,setOffset]=useState(0),[selected,select]=useState<string|null>(null);
  useEffect(()=>{void model.load(record);return()=>model.clear();},[record,model]);
  const review=view.review,scene=review?curationGraphScene(review,side,path,offset):null;
  const node=scene?.details.find(item=>item.node_id===selected);
  const enter=(next:string[])=>{setPath(next);setOffset(0);select(null);};
  return <section className="curation-graph-review" aria-label="Original and proposed research graph">
    <h2>Review the proposed research steps</h2>
    {view.phase!=='ready'&&<p role="status">{view.phase==='loading'?'Reading exact original and proposed graph revisions...':view.phase==='denied'?'Graph details are unavailable to this session.':'The original or proposed graph could not be verified.'}</p>}
    {['failed','denied'].includes(view.phase)&&<button onClick={()=>void model.load(record)}>Retry graph read</button>}
    {review&&<>
      <p>{review.validation?'The saved proposal passed structural validation. Current execution eligibility and scientific validity remain separate.':'This is the retained model proposal. It has not yet been verified as a saved, validated draft.'}</p>
      <div className="curation-graph-toolbar"><div role="group" aria-label="Graph revision"><button aria-pressed={side==='original'} onClick={()=>{setSide('original');setOffset(0);select(null);}}>Original campaign</button>
        <button aria-pressed={side==='proposed'} onClick={()=>{setSide('proposed');setOffset(0);select(null);}}>Proposed campaign</button></div>
        <span>{review.comparison.snapshot.total} structural changes</span></div>
      <h3>{side==='original'?review.original.head.title:review.proposed.title}</h3>
      <nav aria-label="Graph scope"><button onClick={()=>enter([])}>Whole campaign</button>{path.map((id,index)=><button key={index} onClick={()=>enter(path.slice(0,index+1))}>{id}</button>)}</nav>
      {!scene&&<p>This scope is not present in the selected revision. Return to the whole campaign or switch revisions.</p>}
      {scene&&<>
        <div className="curation-graph-toolbar"><label>Inspect scientific step<select value={selected??''} onChange={event=>select(event.target.value||null)}><option value="">Choose a step</option>
          {scene.choices.map((choice,index)=><option key={choice.id+index} value={choice.id}>{choice.label}</option>)}</select></label>
          <span>{scene.nodes.length} of {scene.total} steps · {scene.omittedEdges} connections outside this view</span>
          {scene.total>200&&<><button disabled={!offset} onClick={()=>{setOffset(offset-200);select(null);}}>Previous steps</button><button disabled={offset+200>=scene.total} onClick={()=>{setOffset(offset+200);select(null);}}>More steps</button></>}</div>
        {scene.ambiguous?<p>Duplicate step identities prevent a reliable canvas. Inspect the structural changes and correct the proposal.</p>:
          <div className="curation-graph-canvas"><GraphCanvas fitOnResize key={side+JSON.stringify(path)+offset} label={side==='original'?'Original campaign graph':'Proposed campaign graph'} nodes={scene.nodes} edges={scene.edges} selection={selected} select={select}/></div>}
        <p className="curation-context-summary">Connections show retained control routes and explicit data inputs. Nested steps open their own graph scope.</p>
        {node&&<section className="curation-step-detail" aria-label="Selected research step"><h3>{node.kind==='invoke'?node.tool.capability_id:node.node_id}</h3>
          <p>{node.node_id} · {node.kind}</p>{(node.kind==='scatter'||node.kind==='iterate')&&<button onClick={()=>enter([...path,node.node_id])}>Open nested steps</button>}
          <details><summary>Exact step configuration</summary><pre>{JSON.stringify(node,null,2)}</pre></details></section>}
        <details><summary>Inspect connections in this scope</summary><ul>{scene.edges.map(edge=><li key={edge.id}>{edge.source} → {edge.target} · {edge.label}</li>)}</ul></details>
      </>}
      <details className="curation-technical"><summary>Structural changes and validation details</summary>
        <p>{review.comparison.snapshot.omitted} changes omitted from this bounded list. Structural comparison does not establish scientific compatibility.</p>
        <ol>{review.comparison.snapshot.changes.map((change,index)=><li key={index}><strong>{change.kind} · {change.category}</strong> {change.path}
          <details><summary>Before and after</summary><pre>{JSON.stringify({before:change.before,after:change.after},null,2)}</pre></details></li>)}</ol>
        {review.validation&&<><p>Saved revision {review.validation.revision} · validation {review.validation.validation_id}</p>
          <ul>{review.validation.pending_checks.map(item=><li key={item}>{item}</li>)}</ul></>}
      </details>
      {review.validation&&actions?.(review)}
    </>}
  </section>;
}
