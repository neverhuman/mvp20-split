import { createRoot } from 'react-dom/client';
import { ObservationClient } from '../../src/transport/observations.js';
import { MonitorModel } from '../../src/page_models/monitor.js';
import { NavigationModel } from '../../src/page_models/navigation.js';
import { NamedViewsModel } from '../../src/page_models/named_views.js';
import { EvidenceModel } from '../../src/page_models/evidence.js';
import { MonitorWorkspace } from '../../src/presentation/monitor_workspace.js';
import { context } from '../fixtures/observations.js';
import { AuthoringClient } from '../../src/transport/authoring.js';
import { EmergencyStop } from '../../src/page_models/design/emergency_stop.js';
const client = new ObservationClient();
const model = new MonitorModel(client), navigation = new NavigationModel(client);
const namedViews = new NamedViewsModel(client);
const evidence = new EvidenceModel(client);
const emergency = new EmergencyStop('operator', context, new AuthoringClient());
declare global { interface Window { observationHarness: { model: MonitorModel; navigation: NavigationModel; evidence: EvidenceModel; emergency: EmergencyStop } } }
window.observationHarness = { model, navigation, evidence, emergency };
createRoot(document.getElementById('root')!).render(<MonitorWorkspace model={model} context={context} synthetic
  {...(location.search.includes('navigation=1') ? { navigation, namedViews } : {})}
  {...(location.search.includes('evidence=1') ? { evidence } : {})}
  {...(location.search.includes('emergency=1') ? { emergency } : {})} />);
window.addEventListener('pagehide', () => { model.dispose(); navigation.dispose(); namedViews.dispose(); evidence.dispose(); emergency.dispose(); });
