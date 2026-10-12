import { createRoot } from 'react-dom/client';
import { CurationClient } from '../../src/transport/campaign_curation/client.js';
import { CurationModel } from '../../src/page_models/campaign_curation/model.js';
import { CurationPanel } from '../../src/presentation/campaign_curation/panel.js';
import '../../src/presentation/style.css';
const binding = await fetch('/binding').then(response => response.json());
const model = new CurationModel(new CurationClient());
createRoot(document.getElementById('root')!).render(<CurationPanel model={model} selection={binding}
  synthetic back={() => { location.hash = 'view=design'; }}/ >);
window.addEventListener('pagehide', () => model.dispose());
