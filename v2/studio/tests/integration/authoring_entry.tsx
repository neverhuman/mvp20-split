import { createRoot } from "react-dom/client";
import { AuthoringClient } from "../../src/transport/authoring.js";
import { ObservationClient } from "../../src/transport/observations.js";
import { DraftSession } from "../../src/page_models/design/draft_session.js";
import { DraftCommands } from "../../src/page_models/design/draft_commands.js";
import { EditorCatalog } from "../../src/page_models/design/editor_catalog.js";
import { EmergencyStop } from "../../src/page_models/design/emergency_stop.js";
import { MonitorModel } from "../../src/page_models/monitor.js";
import { DraftWorkspace } from "../../src/presentation/draft_workspace.js";
import { MonitorWorkspace } from "../../src/presentation/monitor_workspace.js";
import type { AuthoringWire, CommandIdentity, CommandReceipt, DraftCommandReceipt } from "../../src/contracts/authoring.js";
import { Submission } from "../../src/transport/submission.js";

const context = JSON.parse(document.getElementById("authoring-context")!.textContent!) as {
  scope: CommandIdentity["scope"]; actor: string; draft: string; mode: string; run: string;
};
const client = new AuthoringClient();
type RetainedSubmission = { identity: CommandIdentity; payload: AuthoringWire["save"] | AuthoringWire["validate"] };
declare global { interface Window { authoringIntegration: { client: AuthoringClient; recover: (submissions: RetainedSubmission[]) => Promise<(CommandReceipt | DraftCommandReceipt)[]>; commands?: DraftCommands; catalog?: EditorCatalog; monitor?: MonitorModel; emergency?: EmergencyStop } } }
window.authoringIntegration = { client, recover: submissions => Promise.all(submissions.map(item => client.receipt(
  new Submission(item.identity.command_family === "definition.save" ? "save" : "validate", item.identity, item.payload), new AbortController().signal))) };
if (context.mode === "cancel") {
  const runContext = { scope: context.scope, run: context.run };
  const monitor = new MonitorModel(new ObservationClient()), emergency = new EmergencyStop(context.actor, runContext, client);
  Object.assign(window.authoringIntegration, { monitor, emergency });
  createRoot(document.getElementById("root")!).render(<MonitorWorkspace model={monitor} context={runContext} emergency={emergency} />);
  window.addEventListener("pagehide", () => { monitor.dispose(); emergency.dispose(); });
} else {
  const base = await client.draft(context.draft, undefined, new AbortController().signal);
  const session = new DraftSession(context.actor, context.scope, context.draft, { title: base.head.title, definition: base.definition }, base);
  const commands = new DraftCommands(session, client), catalog = new EditorCatalog(context.scope, client);
  Object.assign(window.authoringIntegration, { commands, catalog });
  createRoot(document.getElementById("root")!).render(<DraftWorkspace commands={commands} catalog={catalog} />);
  window.addEventListener("pagehide", () => { commands.dispose(); catalog.dispose(); });
}
