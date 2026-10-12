import {useEffect,useMemo,useState} from 'react';
import type {CurationGraphReview} from '../../page_models/campaign_curation/graph_review.js';
import type {RecordedCuration} from '../../page_models/campaign_curation/records.js';
import {CurationNextCycle} from '../../page_models/campaign_curation/next_cycle.js';
import {CurationJournal} from '../../page_models/campaign_curation/journal.js';
import {CurationClient} from '../../transport/campaign_curation/client.js';
import {SuccessorClient} from '../../transport/successor_launch/client.js';
import {SuccessorSources} from '../../transport/successor_launch/sources.js';
import {SuccessorJournal} from '../../page_models/successor_launch/journal.js';
import {SuccessorLaunchModel} from '../../page_models/successor_launch/model.js';
import {SuccessorPreparation} from '../../page_models/successor_launch/preparation.js';
import {LaunchClient} from '../../transport/launch/client.js';
import type {SuccessorSubmission} from '../../transport/successor_launch/submission.js';
import type {SuccessorLaunchReceipt} from '../../contracts/successor_launch.js';
import {SuccessorPanel} from '../campaign_curation/successor.js';

const storage={getItem:(key:string)=>localStorage.getItem(key),setItem:(key:string,value:string)=>localStorage.setItem(key,value)};
export type OpenSuccessor=(review:CurationGraphReview,command:SuccessorSubmission,receipt:SuccessorLaunchReceipt)=>void;
export function CampaignSuccessorEntry({review,open}:{review:CurationGraphReview;open:OpenSuccessor}){
  const record=review.record;
  const owners=useMemo(()=>({preparation:new SuccessorPreparation(new SuccessorSources(),new LaunchClient()),
    launch:new SuccessorLaunchModel(new SuccessorClient(),new SuccessorJournal({actor_id:record.selection.actor,scope:record.selection.reference.scope,
      run_id:record.selection.predecessor,curation_id:record.selection.reference.curation_id},storage))}),[record]);
  useEffect(()=>()=>{owners.preparation.dispose();owners.launch.dispose();},[owners]);
  return <SuccessorPanel review={review} {...owners} open={(command,receipt)=>open(review,command,receipt)}/>;
}
export function CampaignNextCycleEntry({record,ready}:{record:RecordedCuration;ready:()=>void}){
  const [phase,setPhase]=useState<'idle'|'checking'|'failed'>('idle');
  const cycle=useMemo(()=>new CurationNextCycle(new CurationClient(),new CurationJournal({actor_id:record.selection.actor,
    scope:record.selection.reference.scope,run_id:record.selection.predecessor},storage)),[record]);
  useEffect(()=>()=>cycle.dispose(),[cycle]);
  return <section className="curation-next-cycle" aria-label="Prepare another revision"><h2>Explore another idea</h2>
    <p>This preserves the original proposal and prepares a separate request. Existing usage and reservations remain recorded; this is not a refund or retry.</p>
    <button disabled={phase==='checking'} onClick={()=>{setPhase('checking');void cycle.prepare(record).then(ready,()=>setPhase('failed'));}}>Prepare another revision request</button>
    {phase==='checking'&&<p role="status">Verifying that the original request has ended...</p>}
    {phase==='failed'&&<p role="status">The original request could not be verified against this browser's recovery record. It has not been replaced.</p>}
  </section>;
}
