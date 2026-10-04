import { createRoot } from 'react-dom/client';
import { KnowledgeClient } from '../../src/transport/scientific/knowledge.js';
import { ResearchClient } from '../../src/transport/scientific/research.js';
import { ResearchRecordClient } from '../../src/transport/provenance/research.js';
import { DataProvenanceClient } from '../../src/transport/provenance/data.js';
import { ExploreModel } from '../../src/page_models/explore/model.js';
import { ExploreWorkspace } from '../../src/presentation/explore/workspace.js';

const pins = JSON.parse(document.getElementById('explore-context')!.textContent!);
const model = new ExploreModel({ knowledge: new KnowledgeClient(), research: new ResearchClient(),
  records: new ResearchRecordClient(), data: new DataProvenanceClient() });
model.bind(pins);
declare global { interface Window { liveExplore: { model: ExploreModel } } }
window.liveExplore = { model };
createRoot(document.getElementById('root')!).render(<ExploreWorkspace model={model} synthetic />);
window.addEventListener('pagehide', () => model.dispose());
