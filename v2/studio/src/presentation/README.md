# Studio Monitor presentation

UI-01 hosted Monitor exposes authoritative execution status and scoped step count;
inspection history is secondary disclosure. Standalone consumers retain their
expanded controls. The entry shell suppresses duplicate module headers while
preserving module composition. No percentage of scientific progress is inferred.
Runtime node output pages still expose scalar values/artifact references; this
presentation does not deserialize arbitrary scientific artifacts or claim a
campaign-wide candidate ranking. That missing discovery boundary is UI-01/N2.

Scientific views now have a separate [Explore workspace](explore/README.md), owned by BP-06.06. Monitor's Runtime capability catalog remains truthful to its own owner; Explore consumes separately pinned Knowledge/Research/Data projections.

Design: [Studio](../../../docs/Architecture/Experience/Studio.md) and [canvas decision](../../../docs/Architecture/Experience/Studio_Canvas_Decision.md). Implemented: BP-05.02 B1-B3; final-source V1 replacement/audit accepted. User: internal researcher inspecting execution and retained evidence. BP-05.03 adds optional separate emergency-command presentation; scientific acceptance, owner credentials and component-local network reads remain outside this module.

MonitorWorkspace accepts host-owned MonitorModel plus optional NavigationModel, NamedViewsModel and EvidenceModel. The host constructs/disposes network models. React external-store subscriptions render their DTOs; workspace coordinates document visibility and hidden navigation. Its internally owned InspectionHistory has no transport or persistence. Scope/graph/detail/evidence/navigation denial clears affected captured history.

Activation inventory is a bounded list/canvas without inferred links. NavigationPane explicitly opens instantiated iteration/scatter groups and progressive neighborhoods; groups not yet instantiated are labeled. Canvas shows at most200 nodes from a256-node scope, with a second window, omitted counts and outside-window selection. Only verified owner-authored edges whose endpoints are visible are rendered. Pan/zoom are local preferences retained by the navigation model across refresh/unmount; they never mutate topology.

MonitorDetail and EvidencePane expose selected node, bounded attempts, completion, output members and exact Artifact metadata. Loading, unavailable, stale, denied and partial states stay explicit. Runtime retention and tool success are distinct from scientific acceptance. NamedViews exposes scoped Runtime capabilities and predecessor lineage; scientific projections remain visibly unavailable. No global run catalog is implemented.

PinnedInspection consumes a frozen bounded capture without a source port. It displays captured revision/time, omissions, and any captured selected detail outside the graph window. Other node details cannot be fetched in historical mode. Live revision remains separately labeled while pins stay fixed. The history selector allows at most8 local2MiB captures and explicit removal; refreshes never rewrite pins.

GraphCanvas uses React Flow with keyboard/list alternatives and local pan/zoom controls. style.css owns shared typography, focus, contrast, reduced motion and narrow layout. Labels are bounded on canvas; full labels remain in lists/inspectors. The pannable graph is intentional; document-wide horizontal overflow is not.

Verification: `npm run test:browser` (7 Monitor cases, including detail-denial pin clearing), `test:navigation` (10 navigation/history/visibility cases), `test:evidence` (7 linked-evidence failures), `test:dense-navigation` (256-node/six-page branch,long labels,failed node,200/56 windows). Scripted public HTTP peers use the real client/model and receive desktop/narrow A/AA/overflow checks and screenshot review. No instrumented React coverage or full screen-reader conformance claim. [Actual-owner integration](../../tests/integration/README.md) verifies real public records and independent replacement separately.

Replacement preserves model ownership, cut/selection/permission meaning, bounded scenes, omission labels, accessible controls and authored-link provenance. Layout may change; observations cannot become execution commands. Next-campaign drafts are BP-05.03; scientific producers and target-host deployment remain later owners.

Latest acceptance: BP-05.02 closed100%; final-source scopee222d4cf32604d729ef12146860bc49c passes both independently installed65-test browser builds and actual-owner replacement. [Navigation audit](../../../docs/Audits/BP-05.02_Navigation_Closeout.md).

Optional `EmergencyControl` is separate from read-only graph inspection and draft editing. A toolbar link reaches the operational region; historical/stale views disable new stops. It renders EmergencyStop state, original receipt recovery and unresolved external-effect wording. Accepted receipts never rewrite the Monitor projection. No credentials or request logic live in components. `npm run test:emergency` covers acceptance, revision-zero admission, rejection,503 lost acknowledgement, socket loss and denial at desktop/narrow widths, with historical disabling, keyboard invocation, accessibility/overflow checks and screenshots. Owner mutation/race authority is a separate integration gate.

## Design consumer

Internal user task: compose a next-campaign graph, inspect changed bindings/context, save an immutable draft and validate the exact saved revision. Host supplies a selected, scoped DraftCommands session and EditorCatalog and owns their lifecycle/initial draft read. DraftWorkspace remounts transient controls on host-context changes; no global draft picker or application authentication shell is claimed. One bounded canvas and selection inspector own the growing region; shared style tokens/canvas keep keyboard lists and narrow layouts. Nested scopes and200/56 windows handle the public256-node scope bound; duplicate identities require source repair, and omitted/unresolved links are explicit. Canvas layout never writes a definition.

Tool menus use paged reviewed Registry metadata. Input forms change scope-input/node-output bindings; explicit parameter-node creation adds an artifact materializer with exact schema/representation/unit. SchemaFields supplies bounded scalar controls, while structured fields remain explicit bindings. Unapplied/invalid field text is retained. Advanced node/scope source blocks application after concurrent local changes until explicit reload; raw JSON checks numeric lexemes before conversion. Save/validate/receipt requests flow only through DraftCommands, never component-local transport; newer edits survive pending saves. Catalog loading/stale/unavailable/denied states disable unsafe selections; denial clears protected projections and preserves local work. Comparison reports structural differences, not scientific compatibility. The host owns initial loading/error/empty selection before mounting this loaded-session component.

`npm run test:drafts`:8 real Chromium scripted-peer workflows (composition, phone-width keyboard composition,256-node long labels, lost receipt, save conflict, newer pending-save edits, save denial, catalog denial),1440/390 accessibility and overflow scans plus screenshot inspection. Shared GraphCanvas gained directed markers and an explicit Design label;10 navigation/7 Monitor regression cases passed. Actual-owner commands, cancellation races and independent replacement remain separate required gates.

B1 real-owner authoring, exact validation, replacement and separate cancellation passed; two119-test isolated Studio builds. Source/scalar controls have explicit accessible names. [Owner evidence](../../../docs/Audits/Evidence/BP-05-Authoring/Owner.json). Tool-bearing activation and cancel-vs-complete remain B2/B3.

B2 adds an explicit newer-base review comparing remote content to local work. Keeping all local content updates only the expected base and clears old validation; subsequent save/validate are separate actions. Conflict warnings retain local work and hide original-receipt adoption after POST409. Ten Design/seven emergency browser cases pass, including explicit rebase/revalidation and command collisions. [Evidence](../../../docs/Audits/Evidence/BP-05-Authoring/Conflicts.json).

DraftActivationControl offers bounded campaign input bindings and attempt/activation/deadline limits. A current saved/validated draft enables a request, not an execution grant. It renders owner rejection, exact admitted draft/run identity, original receipt recovery, collision and denial separately; draft editing never changes an admitted graph. Fifteen Design browser scenarios pass, including five activation outcomes. Initial bindings use an advanced JSON field; artifact discovery/picking and a global campaign shell are not claimed. Actual owner activation proof passed.

Command settlement uses useCommandFocus for Design, activation and emergency status. It restores keyboard focus from the triggering/disabled control or document body without stealing focus from newer local edits. Confirmed-pending actions offer explicit original-command resume. Sixteen scripted Design browser scenarios pass, including pending resume and conflict focus; this does not establish actual-owner crash recovery.

BP-05.04/B1 integrated actual-owner keyboard/narrow/reconnect journeys passed (scopeb98515e54b7c4a81aa880b83043fdb88). Monitor labels old observation revisions retained whenever its region is not current; unavailable/loading records cannot claim a live revision. Reconnect restores selection and exact detail before live labeling returns.

BP-05.04/B2 production performance is bounded and measured through the real consumer with a synthetic10000-logical source.200 records maximum render/retain; request timing is separate from model/DOM/two-frame settlement. [Owned benchmark](../../tests/browser/README.md) records local hardware, samples, fixed150/250ms regression ceilings and explicit non-SLO/target-host limits.

Local hosting can pass `active=false` to MonitorWorkspace. Browser visibility and
host-mode visibility both suspend observation reads; returning reconciles retained
selection against owner state. Existing callers default to active.

Named execution views now state scientific projection ownership without claiming
that Knowledge/Research projections are globally unimplemented. Local Explore hosts
those separately. Successor lineage remains an immutable Runtime observation; no
scientific validation or improvement is inferred from carried bindings.

UI-01/G1 in progress: Monitor opens the real root topology by default when Navigation
is supplied. Activation inventory is now a secondary list, not an edge-free canvas.
GraphCanvas uses bounded asynchronous ELK geometry with fixed dimensions and actual
routed paths, initial fit, selection emphasis and explicit layout failure. Late
layouts cannot repopulate another scope. Navigation owns per-scope viewport memory.
Graph usability is pending actual-browser qualification; frozen demo unchanged.
