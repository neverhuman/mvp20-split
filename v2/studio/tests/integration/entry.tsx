import { createRoot } from 'react-dom/client';
import { ObservationClient } from '../../src/transport/observations.js';
import { MonitorModel } from '../../src/page_models/monitor.js';
import { MonitorWorkspace } from '../../src/presentation/monitor_workspace.js';
import type { RunContext } from '../../src/page_models/graph_window.js';
import { NavigationModel } from '../../src/page_models/navigation.js';
import { NamedViewsModel } from '../../src/page_models/named_views.js';
import { EvidenceModel } from '../../src/page_models/evidence.js';
const context = JSON.parse(document.getElementById('observation-context')!.textContent!) as RunContext;
const client = new ObservationClient();
const model = new MonitorModel(client);
const navigation = new NavigationModel(client), namedViews = new NamedViewsModel(client), evidence = new EvidenceModel(client);
declare global { interface Window { integrationHarness: { model: MonitorModel; client: ObservationClient; navigation: NavigationModel; namedViews: NamedViewsModel; evidence: EvidenceModel } } }
window.integrationHarness = { model, client, navigation, namedViews, evidence };
createRoot(document.getElementById('root')!).render(<MonitorWorkspace model={model} context={context} navigation={navigation} namedViews={namedViews} evidence={evidence} synthetic />);
window.addEventListener('pagehide', () => { model.dispose(); navigation.dispose(); namedViews.dispose(); evidence.dispose(); });
