import { createRoot } from 'react-dom/client';
import { SessionClient } from './transport/session/client.js';
import { WorkspaceSession } from './page_models/session/model.js';
import { LocalWorkspace } from './presentation/entry/workspace.js';

function takeTicket() {
  const fragment = new URLSearchParams(location.hash.slice(1));
  const ticket = fragment.get('launch') ?? undefined;
  if (location.hash) history.replaceState(null, '', location.pathname + location.search);
  return ticket;
}
const session = new WorkspaceSession(new SessionClient());
createRoot(document.getElementById('root')!).render(<LocalWorkspace session={session} />);
void session.open(takeTicket());
window.addEventListener('hashchange', () => { const ticket=takeTicket(); if (ticket) void session.open(ticket); });
window.addEventListener('pagehide', () => session.dispose());
