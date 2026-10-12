import { useEffect,useMemo } from 'react';
import type { WorkspaceContext } from '../../transport/session/client.js';
import type { LaunchPlanningContext } from '../../page_models/launch/planning_context.js';
import type { CurationSelection } from '../../transport/campaign_curation/identity.js';
import { CurationCommands } from '../../transport/campaign_curation/commands.js';
import { CurationRequestModel } from '../../page_models/campaign_curation/request.js';
import { CurationJournal } from '../../page_models/campaign_curation/journal.js';
import { CurationPreparation,OriginalCurationContext } from '../../page_models/campaign_curation/preparation.js';
import { ObservationClient } from '../../transport/observations.js';
import { AuthoringClient } from '../../transport/authoring.js';
import { CampaignOriginClient } from '../../transport/campaign_origin/client.js';
import { OriginReader } from '../../page_models/campaign_origin/reader.js';
import { CurationComposer } from '../campaign_curation/composer.js';

// Reviewed internal deployment binding. Planning's configured policy remains authority;
// this public identifier conveys no provider, credentials or spending override.
export const INTERNAL_CURATION_POLICY='internal-curation-v1';

export function CampaignCurationEntry({context,planning,review}:{context:WorkspaceContext&{run_id:string};planning?:LaunchPlanningContext;
  review:(selection:CurationSelection)=>void}){
  const owners=useMemo(()=>{
    if(!planning)return null;
    const origin=new OriginReader(new CampaignOriginClient(),new AuthoringClient());
    return {request:new CurationRequestModel(new CurationCommands(),new CurationJournal(context,
      {getItem:key=>localStorage.getItem(key),setItem:(key,value)=>localStorage.setItem(key,value)})),
      preparation:new CurationPreparation(context,INTERNAL_CURATION_POLICY,new ObservationClient(),new OriginalCurationContext(planning,origin))};
  },[context.actor_id,context.scope.tenant_id,context.scope.project_id,context.run_id,planning]);
  useEffect(()=>()=>{owners?.request.dispose();owners?.preparation.dispose();},[owners]);
  if(!owners)return <section aria-label="Request a campaign revision"><h2>Revision context not linked</h2>
    <p>Start a prepared campaign from this workspace to retain its exact draft link for model-guided revision. This historical run remains available for inspection.</p></section>;
  return <CurationComposer {...owners} synthetic={context.synthetic} review={review}/>;
}
