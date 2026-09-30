import { createRoot } from 'react-dom/client';
import { ObservationClient } from '../../src/transport/observations.js';
import { MonitorModel } from '../../src/page_models/monitor.js';
import { NavigationModel } from '../../src/page_models/navigation.js';
import { NamedViewsModel } from '../../src/page_models/named_views.js';
import { MonitorWorkspace } from '../../src/presentation/monitor_workspace.js';
import { context } from '../fixtures/observations.js';
const client = new ObservationClient();
const model = new MonitorModel(client), navigation = new NavigationModel(client);
const namedViews = new NamedViewsModel(client);
declare global { interface Window { observationHarness: { model: MonitorModel; navigation: NavigationModel } } }
window.observationHarness = { model, navigation };
createRoot(document.getElementById('root')!).render(<MonitorWorkspace model={model} context={context} synthetic
  {...(location.search.includes('navigation=1') ? { navigation, namedViews } : {})} />);
window.addEventListener('pagehide', () => { model.dispose(); navigation.dispose(); namedViews.dispose(); });
