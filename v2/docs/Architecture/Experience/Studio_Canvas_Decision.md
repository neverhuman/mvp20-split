# Studio Canvas Decision

Design status: selected for the first Studio implementation at `2026-09-29 19:40:45` (America/Chicago). Parent: [Studio](Studio.md). Scope: BP-05.01/B2, not live Runtime integration or scientific acceptance.

Use React 19.3.0 and React Flow 12.12.0 for the first campaign canvas. Retain Cytoscape 3.34.3 as a development-only comparison candidate. Dependencies are exact-pinned in the Studio lockfile. This is a replaceable presentation decision; neither package owns execution, scientific relationships or authoritative run state.

Both candidates ran the same 200-node window against a server-side 10,000-node synthetic source, shared selection/viewport model, searchable semantic list and read-only inspector. Both passed scoped keyboard/list journeys, bounded pagination/search, selection and viewport preservation, explicit reveal, long labels, narrow layout and automated WCAG A/AA checks at 1440×1000 and 390×844. React Flow additionally passed native graph-node focus/Enter selection, which feeds the same inspector. Its first implementation needed controlled selection change handling; competing selection callbacks were removed after a browser regression exposed stale selection overwrite.

| Local headless Chromium 153 sample | React Flow | Cytoscape |
|---|---:|---:|
| Initial load median, five runs | 160.71 ms | 133.98 ms |
| Page update median, five runs | 167.13 ms | 116.01 ms |
| Initial load range | 148.54–547.88 ms | 116.06–204.36 ms |
| Page update range | 151.75–266.30 ms | 99.48–139.76 ms |
| Automated accessibility violations, both viewports | 0 | 0 |

These are harness wall-clock measurements including browser actions, HTTP, rendering and two animation frames. The first load includes cold work; five samples do not establish a latency percentile, throughput limit or production SLA. Source generation uses explicit fixture topology; existing Runtime activation order does not establish edges. Only 200 records enter a scene; the canvas pans through them rather than fitting all labels into a single screenshot.

Cytoscape was faster in this sample. React Flow is selected because individually focusable DOM nodes and customizable node/port presentation suit the next-campaign editor, while its measured bounded-scene behavior remains practical for this internal prototype. Native graph keyboard interaction complements the mandatory list rather than replacing it. Full graph authoring, typed connections, persisted layouts and active-run authority are not proved by this spike. The comparison is not evidence that React Flow is universally faster or appropriate for an unbounded knowledge graph.

Observed visual defects were repaired before this checkpoint: narrow-screen attribution contrast and long-label overlap. Full labels remain in the inspector/list while canvas text is bounded. Graph navigation preserves the viewport by default; explicit Show window/Show selected node controls move it deliberately. Essential actions have semantic keyboard controls and focus indicators. Actual desktop/narrow screenshots were inspected; screen-reader usability remains a later evaluation.

The [prototype module](../../../studio/spikes/interaction/README.md) owns reproduction and replacement boundaries. [B2 evidence](../../Audits/Evidence/BP-05-Interaction/B2.json) records exact browser samples and independent source build. B3 must use the real browser transport/page model for slow detail, stale response, denied scope, empty and expired-cursor cases. V1 must connect to actual available owners. This decision cannot substitute fixture screenshots for those gates.

Primary library references: [React Flow accessibility](https://reactflow.dev/learn/advanced-use/accessibility), [React Flow component contract](https://reactflow.dev/api-reference/react-flow), [Cytoscape public API](https://js.cytoscape.org/). Measured behavior above comes from the local harness, not library marketing or third-party benchmarks.
