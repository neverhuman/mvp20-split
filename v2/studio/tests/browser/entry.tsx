import { createRoot } from 'react-dom/client';
import { ObservationClient } from '../../src/transport/observations.js';
import { MonitorModel } from '../../src/page_models/monitor.js';
import { NavigationModel } from '../../src/page_models/navigation.js';
import { NamedViewsModel } from '../../src/page_models/named_views.js';
import { EvidenceModel } from '../../src/page_models/evidence.js';
import { MonitorWorkspace } from '../../src/presentation/monitor_workspace.js';
import { context } from '../fixtures/observations.js';
const client = new ObservationClient();
const model = new MonitorModel(client), navigation = new NavigationModel(client);
const namedViews = new NamedViewsModel(client);
const evidence = new EvidenceModel(client);
declare global { interface Window { observationHarness: { model: MonitorModel; navigation: NavigationModel; evidence: EvidenceModel } } }
window.observationHarness = { model, navigation, evidence };
createRoot(document.getElementById('root')!).render(<MonitorWorkspace model={model} context={context} synthetic
  {...(location.search.includes('navigation=1') ? { navigation, namedViews } : {})}
  {...(location.search.includes('evidence=1') ? { evidence } : {})} />);
window.addEventListener('pagehide', () => { model.dispose(); navigation.dispose(); namedViews.dispose(); evidence.dispose(); });
