# Studio Monitor presentation

Design: [Studio](../../../docs/Architecture/Experience/Studio.md) and [canvas decision](../../../docs/Architecture/Experience/Studio_Canvas_Decision.md). Implemented: BP-05.02 B1-B3; final-source V1 replacement/audit accepted. User: internal researcher inspecting execution and retained evidence. No execution commands, scientific acceptance, owner credentials or component-local network reads.

MonitorWorkspace accepts host-owned MonitorModel plus optional NavigationModel, NamedViewsModel and EvidenceModel. The host constructs/disposes network models. React external-store subscriptions render their DTOs; workspace coordinates document visibility and hidden navigation. Its internally owned InspectionHistory has no transport or persistence. Scope/graph/detail/evidence/navigation denial clears affected captured history.

Activation inventory is a bounded list/canvas without inferred links. NavigationPane explicitly opens instantiated iteration/scatter groups and progressive neighborhoods; groups not yet instantiated are labeled. Canvas shows at most200 nodes from a256-node scope, with a second window, omitted counts and outside-window selection. Only verified owner-authored edges whose endpoints are visible are rendered. Pan/zoom are local preferences retained by the navigation model across refresh/unmount; they never mutate topology.

MonitorDetail and EvidencePane expose selected node, bounded attempts, completion, output members and exact Artifact metadata. Loading, unavailable, stale, denied and partial states stay explicit. Runtime retention and tool success are distinct from scientific acceptance. NamedViews exposes scoped Runtime capabilities and predecessor lineage; scientific projections remain visibly unavailable. No global run catalog is implemented.

PinnedInspection consumes a frozen bounded capture without a source port. It displays captured revision/time, omissions, and any captured selected detail outside the graph window. Other node details cannot be fetched in historical mode. Live revision remains separately labeled while pins stay fixed. The history selector allows at most8 local2MiB captures and explicit removal; refreshes never rewrite pins.

GraphCanvas uses React Flow with keyboard/list alternatives and local pan/zoom controls. style.css owns shared typography, focus, contrast, reduced motion and narrow layout. Labels are bounded on canvas; full labels remain in lists/inspectors. The pannable graph is intentional; document-wide horizontal overflow is not.

Verification: `npm run test:browser` (7 Monitor cases, including detail-denial pin clearing), `test:navigation` (10 navigation/history/visibility cases), `test:evidence` (7 linked-evidence failures), `test:dense-navigation` (256-node/six-page branch,long labels,failed node,200/56 windows). Scripted public HTTP peers use the real client/model and receive desktop/narrow A/AA/overflow checks and screenshot review. No instrumented React coverage or full screen-reader conformance claim. [Actual-owner integration](../../tests/integration/README.md) verifies real public records and independent replacement separately.

Replacement preserves model ownership, cut/selection/permission meaning, bounded scenes, omission labels, accessible controls and authored-link provenance. Layout may change; observations cannot become execution commands. Next-campaign drafts are BP-05.03; scientific producers and target-host deployment remain later owners.

Latest acceptance: BP-05.02 closed100%; final-source scopee222d4cf32604d729ef12146860bc49c passes both independently installed65-test browser builds and actual-owner replacement. [Navigation audit](../../../docs/Audits/BP-05.02_Navigation_Closeout.md).
