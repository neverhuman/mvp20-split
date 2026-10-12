import {useEffect} from 'react';
import type {SupervisionModel} from '../../page_models/supervision/model.js';
import type {RunContext} from '../../page_models/graph_window.js';
import {SupervisionInspector} from '../supervision/inspector.js';
import './style.css';
/** One existing owner model, separately scoped from the technical monitor's lifecycle. */
export function CampaignReasoning({model,context,back}:{model:SupervisionModel;context:RunContext;back:()=>void}){
 useEffect(()=>{model.bind(context);void model.refresh();return()=>model.invalidate();},[model,context.scope.tenant_id,context.scope.project_id,context.run]);
 return <section className="campaign-reasoning" aria-label="Recorded campaign decisions"><button onClick={back}>Return to results</button><h1>What did the model recommend?</h1>
  <p>Follow a retained request to its recorded response and the outcome committed by Runtime. A recommendation, an abstention and an accepted execution decision have different meanings.</p>
  <p>This view reads existing campaign history. It does not call a model or change the running campaign.</p>
  <SupervisionInspector model={model}/>
 </section>;
}
