import {useCallback,useEffect,useMemo,useState,useSyncExternalStore} from 'react';
import type {GraphNodeDetail,GraphSnapshotPage} from '../../contracts/observations.js';
import type {CandidateInspection} from '../../page_models/candidate_inspector/model.js';
import {CandidateInspectorModel} from '../../page_models/candidate_inspector/model.js';
import {CandidateClient} from '../../transport/candidate/client.js';
import {DataProvenanceClient} from '../../transport/provenance/data.js';
import './style.css';

export function CandidateDetails({inspection,inspectExecution}:{inspection:CandidateInspection;inspectExecution?:()=>void}){
 const outcome=inspection.result.outcome,candidate=inspection.result.candidate;
 const [imageFailed,setImageFailed]=useState(false),[executionOpen,setExecutionOpen]=useState(false);
 return <article className="candidate-detail" aria-label="Candidate structure">
  <header><p className="eyebrow">Supplied structure · {inspection.recommendation?'Unranked candidate':'Structure unavailable'}</p><h3>{candidate.candidate_id}</h3><p>Revision {candidate.revision} · fully specified finite molecule</p></header>
  {outcome.status!=='derived'?<p role="status">The structure tool reported {outcome.status}: {outcome.code.replaceAll('_',' ')}. No formula or depiction is available.</p>:<>
   <div className="candidate-shape"><div><p className="eyebrow">Molecular formula</p><p className="candidate-formula">{outcome.formula.text}</p><p>Net formal charge: {outcome.formula.net_formal_charge}</p><p>2D connectivity; no 3D conformation implied.</p></div>
    {imageFailed?<p role="status">The verified image could not be displayed by this browser.</p>:inspection.depiction&&<img src={inspection.depiction} width={outcome.depiction.width} height={outcome.depiction.height} alt={`Two-dimensional structure of supplied candidate ${candidate.candidate_id}, molecular formula ${outcome.formula.text}`} onError={()=>setImageFailed(true)}/>}</div>
   {outcome.warnings.length>0&&<p className="candidate-warning">Some stereochemistry is unspecified in the supplied structure.</p>}
   <div className="candidate-evidence-summary"><section><h4>Why unranked?</h4><p>No molecular selection policy or comparative evaluation is attached to this result. A valid structure is not a recommendation.</p></section><section><h4>Properties</h4><p>No linked predicted or measured property evidence.</p></section><section><h4>Can it be synthesized?</h4><p>No linked synthesis-feasibility assessment.</p></section></div>
   <details><summary>Structure and derivation</summary><dl><div><dt>Canonical isomeric SMILES</dt><dd><code>{outcome.canonical_isomeric_smiles}</code></dd></div><div><dt>Method</dt><dd>{outcome.method.method} · {outcome.method.toolkit} {outcome.method.toolkit_version}</dd></div><div><dt>Formula semantics</dt><dd>Separate isotopes; explicit net formal charge. Exact finite structure, not an unspecified polymer repeat unit.</dd></div><div><dt>Environment SHA-256</dt><dd><code>{outcome.method.environment_sha256}</code></dd></div></dl></details>
  </>}
  <details><summary>Execution and artifact provenance</summary><dl>
   <div><dt>Producing tool</dt><dd>{inspection.execution.invocation.tool.capability_id} / {inspection.execution.invocation.tool.release}</dd></div>
   <div><dt>Run and step</dt><dd>{inspection.execution.completion.run_id} / {inspection.execution.invocation.node_id}</dd></div>
   <div><dt>Accepted completion</dt><dd>{inspection.execution.completion.completion_id} · revision {inspection.execution.completion.accepted_run_revision}</dd></div>
   <div><dt>Source artifact</dt><dd>{inspection.source.artifact_id}<br/><code>{inspection.source.sha256}</code></dd></div>
   <div><dt>Structure artifact</dt><dd>{inspection.representation.artifact_id}<br/><code>{inspection.representation.sha256}</code></dd></div>
   <div><dt>Candidate lineage</dt><dd>{inspection.candidate?.supersedes?`Supersedes candidate revision ${inspection.candidate.supersedes.revision}`:'No predecessor candidate revision recorded.'}</dd></div>
  </dl></details>
  <button aria-expanded={executionOpen} onClick={()=>{setExecutionOpen(!executionOpen);inspectExecution?.();}}>{executionOpen?'Close producing execution step':'Inspect producing execution step'}</button>
  {executionOpen&&<section aria-label="Producing execution step"><h4>{inspection.node.path.node_id}</h4><p>{inspection.node.status} at retained Runtime revision {inspection.cut.revision}. This inspection stays at the candidate's read snapshot.</p><dl>
   <div><dt>Activation</dt><dd>{inspection.node.activation_id}</dd></div><div><dt>Occurrence</dt><dd>{inspection.node.path.occurrences?.length?(inspection.node.path.occurrences??[]).map(o=>`${o.node_id} [${o.index}]`).join(' / '):'Root graph'}</dd></div>
   <div><dt>Accepted attempt</dt><dd>{inspection.execution.completion.result.attempt_id} · fence {inspection.execution.completion.result.fence}</dd></div><div><dt>Worker</dt><dd>{inspection.execution.worker_id}</dd></div><div><dt>Plan digest</dt><dd><code>{inspection.cut.plan_sha256}</code></dd></div>
  </dl><p>Execution acceptance confirms the producing step, not chemical efficacy or synthesis feasibility.</p></section>}
 </article>;
}

export function CandidateInspector({anchor,detail,inspectExecution}:{anchor:GraphSnapshotPage['snapshot']|null;detail:GraphNodeDetail|null;inspectExecution?:()=>void}){
 const model=useMemo(()=>{const owners=new CandidateClient(),data=new DataProvenanceClient();return new CandidateInspectorModel({producer:(...args)=>owners.producer(...args),candidate:(...args)=>owners.candidate(...args),jsonArtifact:(...args)=>data.jsonArtifact(...args)});},[]);
 const listen=useCallback((notify:()=>void)=>model.subscribe(notify),[model]),view=useSyncExternalStore(listen,()=>model.snapshot);
 useEffect(()=>{void model.read(anchor,detail);return()=>{void model.read(null,null);};},[model,anchor,detail]);
 useEffect(()=>()=>model.dispose(),[model]);
 if(view.phase==='idle')return null;
 return <section className="candidate-inspector" aria-label="Verified candidate inspection">{view.inspection?<CandidateDetails key={view.inspection.representation.sha256} inspection={view.inspection} {...(inspectExecution?{inspectExecution}:{})}/>:<p role="status">{view.phase==='loading'?'Verifying the candidate, accepted execution and structure bytes…':view.error}</p>}</section>;
}
