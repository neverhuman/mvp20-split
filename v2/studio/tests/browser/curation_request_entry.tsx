import { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CurationRequestModel } from '../../src/page_models/campaign_curation/request.js';
import { CurationJournal } from '../../src/page_models/campaign_curation/journal.js';
import { CurationPreparation } from '../../src/page_models/campaign_curation/preparation.js';
import { CurationCommands } from '../../src/transport/campaign_curation/commands.js';
import { ObservationClient } from '../../src/transport/observations.js';
import { CurationComposer } from '../../src/presentation/campaign_curation/composer.js';
import { CurationPanel } from '../../src/presentation/campaign_curation/panel.js';
import { CurationModel } from '../../src/page_models/campaign_curation/model.js';
import { CurationClient } from '../../src/transport/campaign_curation/client.js';
import type { CurationSelection } from '../../src/transport/campaign_curation/identity.js';
import '../../src/presentation/style.css';
const binding=await fetch('/binding').then(response=>response.json());
const request=new CurationRequestModel(new CurationCommands(),new CurationJournal(binding.actor,localStorage));
const preparation=new CurationPreparation(binding.actor,'synthetic',new ObservationClient(),{read:async()=>binding.context});
const model=new CurationModel(new CurationClient());
function Fixture(){const [selection,setSelection]=useState<CurationSelection|null>(null);
  return selection?<CurationPanel model={model} selection={selection} synthetic back={()=>setSelection(null)}/>:
    <main style={{maxWidth:1000,margin:'auto',padding:24}}><h1>Improve the next campaign</h1>
      <CurationComposer request={request} preparation={preparation} review={setSelection} synthetic/></main>;
}
createRoot(document.getElementById('root')!).render(<Fixture/>);
window.addEventListener('pagehide',()=>{request.dispose();preparation.dispose();model.dispose();});
