import { createRoot } from "react-dom/client";
import { AuthoringClient } from "../../src/transport/authoring.js";
import { DraftSession } from "../../src/page_models/design/draft_session.js";
import { DraftCommands } from "../../src/page_models/design/draft_commands.js";
import { EditorCatalog } from "../../src/page_models/design/editor_catalog.js";
import { DraftWorkspace } from "../../src/presentation/draft_workspace.js";
import { scope } from "../fixtures/authoring.js";

declare global { interface Window { draftHarness: { commands: DraftCommands; catalog: EditorCatalog } } }
const client = new AuthoringClient();
const base = await client.draft("draft", undefined, new AbortController().signal);
const session = new DraftSession("researcher", scope, "draft", { title: base.head.title, definition: base.definition }, base);
const commands = new DraftCommands(session, client), catalog = new EditorCatalog(scope, client);
window.draftHarness = { commands, catalog };
createRoot(document.getElementById("root")!).render(<DraftWorkspace commands={commands} catalog={catalog} synthetic />);
window.addEventListener("pagehide", () => { commands.dispose(); catalog.dispose(); });
