# Local workspace entry

Owns the compact application identity/local-access strip and session states.
WorkspaceSession owns loading, denial and failure. An authenticated session with
no selected run renders an explicit empty view; it does not fabricate a sample or
claim that no campaign exists on the backend. A selected run reuses Monitor's
existing graph, navigation and evidence models and styles. Each model is disposed
on context replacement. No owner fetches live in presentation components.

This first hosting entry exposes Monitor. Design/Explore application navigation,
emergency controls and integrated demo context selection remain explicit assembly
work; their existing components are not rewritten. Browser acceptance must check
entry/session/error/empty states and monitor rendering at desktop/narrow widths.
