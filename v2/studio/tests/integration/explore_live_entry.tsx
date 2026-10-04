import { createRoot } from 'react-dom/client';
import { KnowledgeClient } from '../../src/transport/scientific/knowledge.js';
import { ResearchClient } from '../../src/transport/scientific/research.js';
import { ResearchRecordClient } from '../../src/transport/provenance/research.js';
import { DataProvenanceClient } from '../../src/transport/provenance/data.js';
import { ExploreModel } from '../../src/page_models/explore/model.js';
import { ExploreWorkspace } from '../../src/presentation/explore/workspace.js';

import { FeedbackClient } from '../../src/transport/feedback/client.js';
import { FeedbackModel } from '../../src/page_models/feedback/model.js';

const pins = JSON.parse(document.getElementById('explore-context')!.textContent!);
const model = new ExploreModel({ knowledge: new KnowledgeClient(), research: new ResearchClient(),
  records: new ResearchRecordClient(), data: new DataProvenanceClient() });
model.bind(pins.explore);
const feedback = pins.feedback ? new FeedbackModel({ research: new ResearchRecordClient(), feedback: new FeedbackClient() }) : null;
feedback?.bind(pins.feedback);
declare global { interface Window { liveExplore: { model: ExploreModel; feedback: FeedbackModel | null } } }
window.liveExplore = { model, feedback };
createRoot(document.getElementById('root')!).render(<ExploreWorkspace model={model} {...(feedback ? { feedback } : {})} synthetic />);
window.addEventListener('pagehide', () => { model.dispose(); feedback?.dispose(); });
