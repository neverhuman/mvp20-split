import { createRoot } from 'react-dom/client';
import { ObservationClient } from '../../src/transport/observations.js';
import { MonitorModel } from '../../src/page_models/monitor.js';
import { MonitorWorkspace } from '../../src/presentation/monitor_workspace.js';
import { context } from '../fixtures/observations.js';
const model = new MonitorModel(new ObservationClient());
declare global { interface Window { observationHarness: { model: MonitorModel } } }
window.observationHarness = { model };
createRoot(document.getElementById('root')!).render(<MonitorWorkspace model={model} context={context} synthetic />);
window.addEventListener('pagehide', () => model.dispose());
