import {useCallback,useEffect,useMemo,useSyncExternalStore} from 'react';
import type {ArtifactRef} from '../contracts/observations.js';
import {DataProvenanceClient} from '../transport/provenance/data.js';
import {ScientificOutputModel,supported} from '../page_models/scientific_output/model.js';

/** One selected, verified scientific output; no inferred assessment or generic JSON dump. */
export function ScientificOutput({reference}:{reference:ArtifactRef|null}){
  const model=useMemo(()=>new ScientificOutputModel(new DataProvenanceClient()),[]);
  const subscribe=useCallback((f:()=>void)=>model.subscribe(f),[model]);const view=useSyncExternalStore(subscribe,()=>model.snapshot);
  const identity=reference?JSON.stringify(reference):'';
  useEffect(()=>{void model.read(reference);return()=>{void model.read(null);};},[model,identity]);
  useEffect(()=>()=>model.dispose(),[model]);
  if(!reference||!supported(reference))return null;
  const result=view.result;
  return <section aria-label="Scientific calculation result" className="scientific-result">
    <h2>{reference.schema_ref.schema_id==='materials.hansen-solvency.output'?'Hansen solvency screen':'Temperature-adjusted viscosity'}</h2>
    <p className="eyebrow">Actual calculation / unvalidated screen</p>
    {!result?<p role="status">{view.phase==='loading'?'Verifying retained result...':view.error??'No verified result loaded.'}</p>:<>
      <h3>{result.candidate}</h3><dl>{result.quantities.map(q=><div key={q.name}><dt>{q.name.replaceAll('_',' ')}</dt><dd><strong>{typeof q.value==='number'?Number(q.value.toPrecision(7)):q.value}</strong> {q.unit}</dd></div>)}</dl>
      <h3>Calculation steps</h3><ol>{result.procedure.map((s,i)=><li key={i}>{s}</li>)}</ol>
      <h3>Limits of this result</h3><p>{result.limitation}</p>
      <details><summary>Retained input parameters</summary><dl>{Object.entries(result.parameters).map(([key,value])=><div key={key}><dt>{key.replaceAll('_',' ')}</dt><dd>{typeof value==='object'?Object.entries(value as Record<string,unknown>).map(([k,v])=>`${k}: ${v}`).join('; '):String(value)}</dd></div>)}</dl></details>
      <p className="muted">Artifact content and schema hashes verified. Execution success is separate from scientific validity.</p>
    </>}
  </section>;
}
