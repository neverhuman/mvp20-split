# SME evaluation review surface

Primary question: is this a defensible way to evaluate candidate structures?
The page renders EvaluationReview's bounded local document through GraphCanvas,
with selectable objective/criterion/method/selection/iteration steps and an
accessible button list. The inspector exposes scientific method choices, inputs,
expected outputs, applicability, assumptions, evidence, rules and source provenance.
Connections are proposed reasoning/dependency relationships, not execution events.

Synthetic demo sessions start with an explicitly Codex-authored polymer proposal.
Other sessions require file import. Imported provenance is unverified declared
authorship; content remains inert React text, never HTML/URLs executed by the app.
No network requests, campaign mutations or model calls belong to this component.
The surrounding authenticated workspace owns access/lifetime; no local storage.

Review notes export/import with the original design for a future campaign.
All replacement imports require an explicit replacement action. Invalid imports
preserve existing work; stale file reads cannot replace newer requests. Navigation
retains the mounted review. Reload loses unexported work and triggers an unload
warning when notes exist. Unsaved form text is temporary per selected node.

Browser verification owns SME concern entry, export/reimport, graph inspection,
desktop/narrow accessibility and distinction from numerical execution history.
The local artifact is not a Runtime draft, not an LLM provider receipt, and not
automatically consumed by next-campaign planning. Those require a separate adapter.
