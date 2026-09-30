import { createRoot } from 'react-dom/client';
import { ObservationClient } from '../../src/transport/observations.js';
import { MonitorModel } from '../../src/page_models/monitor.js';
import { MonitorWorkspace } from '../../src/presentation/monitor_workspace.js';
import type { RunContext } from '../../src/page_models/graph_window.js';
const context = JSON.parse(document.getElementById('observation-context')!.textContent!) as RunContext;
const client = new ObservationClient();
const model = new MonitorModel(client);
declare global { interface Window { integrationHarness: { model: MonitorModel; client: ObservationClient } } }
window.integrationHarness = { model, client };
createRoot(document.getElementById('root')!).render(<MonitorWorkspace model={model} context={context} synthetic />);
window.addEventListener('pagehide', () => model.dispose());
