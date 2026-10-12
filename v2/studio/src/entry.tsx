import { createRoot } from 'react-dom/client';
import { SessionClient } from './transport/session/client.js';
import { WorkspaceSession } from './page_models/session/model.js';
import { LocalWorkspace } from './presentation/entry/workspace.js';

function takeLink() {
  const fragment = new URLSearchParams(location.hash.slice(1));
  const ticket = fragment.get('launch') ?? undefined;
  const selection = new URLSearchParams();
  for (const key of ['explore', 'feedback', 'quality_output', 'curation', 'view'])
    for (const value of fragment.getAll(key)) selection.append(key, value);
  // Retain non-secret navigation pins for reload; erase the one-use credential.
  if (location.hash) history.replaceState(null, '', location.pathname + (selection.size ? '#' + selection : ''));
  return { ticket, selection:selection.toString() };
}
const session = new WorkspaceSession(new SessionClient());
const root = createRoot(document.getElementById('root')!);
function renderLink(initial = false) {
  const link = takeLink();
  root.render(<LocalWorkspace session={session} search={link.selection} />);
  if (initial || link.ticket) void session.open(link.ticket);
}
renderLink(true);
window.addEventListener('hashchange', () => renderLink());
window.addEventListener('pagehide', () => session.dispose());
