import {createRoot} from 'react-dom/client';
import {useMemo,useState} from 'react';
import {CurationPanel} from '../../src/presentation/campaign_curation/panel.js';
import {CurationModel} from '../../src/page_models/campaign_curation/model.js';
import {CurationGraphModel} from '../../src/page_models/campaign_curation/graph_model.js';
import {CurationGraphReader} from '../../src/page_models/campaign_curation/graph_review.js';
import {CurationClient} from '../../src/transport/campaign_curation/client.js';
import {AuthoringClient} from '../../src/transport/authoring.js';
import {CampaignSuccessorEntry,CampaignNextCycleEntry} from '../../src/presentation/entry/successor.js';
import type {CurationSelection} from '../../src/transport/campaign_curation/identity.js';
import '../../src/presentation/style.css';

function App({selection}:{selection:CurationSelection}){
  const [opened,setOpened]=useState<string|null>(null),[next,setNext]=useState(false);
  const owners=useMemo(()=>({model:new CurationModel(new CurationClient()),graphs:new CurationGraphModel(new CurationGraphReader(new AuthoringClient()))}),[]);
  if(opened)return <main><h1>Opened successor {opened}</h1></main>;
  if(next)return <main><h1>Ready for a different research direction</h1></main>;
  return <CurationPanel {...owners} selection={selection} synthetic back={()=>{}}
    successor={review=><CampaignSuccessorEntry review={review} open={(_review,_command,receipt)=>setOpened(receipt.run_id)}/>}
    nextCycle={record=><CampaignNextCycleEntry record={record} ready={()=>setNext(true)}/>}/>;
}
const setup=await(await fetch('/binding')).json();
if(!localStorage.getItem('fixture-seeded')){localStorage.setItem(setup.storageKey,JSON.stringify({version:1,body:setup.body}));localStorage.setItem('fixture-seeded','yes');}
createRoot(document.getElementById('root')!).render(<App selection={setup.selection}/>);
