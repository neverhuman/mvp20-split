# Installed graph acceptance

- Owner: Campaign Runtime scheduling acceptance, BP-04.02/V1.
- Status: eight actual installed scenarios passed; scope bab36cf644df43e59a370437d68c94d1, reviewed 2026-09-28 19:47:08.

Run `dev/verify_graphs.py --images <verified tool-image manifest>` with the explicit owned PostgreSQL fixture opt-in. The driver builds the public dependency closure and creates independent Registry, Runtime, Artifact, SDK and two tool environments plus a fresh Runtime replacement. It verifies the scientific tool wheel hashes against the separately retained Linux image manifest. No startup migration or database reset is performed.

The controller runs in an isolated SDK interpreter. Reused integration-owned helpers launch peers, publish inputs, register/activate exact tool descriptors and heartbeat replicas through public HTTP. Owner SQL credentials are passed only to their respective service processes; scientific workers and the compiler probe receive none. The Runtime compiler probe uses its own installed package and public contract roots, not adjacent owner implementations.

Scenarios execute direct numeric and symbol tools, an Artifact-backed branch predicate/all-member join, two tool-bearing iterations, empty scatter and parallel scatter. Runtime replacement occurs while workers are paused after actual Artifact publication and before completion. Completion order is reversed, one success reply is dropped, and the SDK must recover the original receipt. Retained graph observations and output bytes from earlier runs are checked after replacement. Barriers and response loss are test-only wrappers around actual public boundaries; no canonical result is fabricated.

Evidence is credential-free under `.test-results/graph-acceptance/<scope>/`; full bodies are limited to synthetic fixtures, public records and compiled plans. The Windows installed-process tier is separate from Linux non-root image goldens and does not claim Linux-to-owner deployment, K3s, target-host durability or scientific efficacy. All owned process trees are closed, and failure cleanup may cancel only this harness's active run.

The final gate also runs the installed coordinate CLI to close a graph autonomously and the installed delivery CLI to acknowledge all seven accepted Artifact confirmations. No notification target is configured; those notifications are not claimed delivered. [Preserved evidence](../../../../../docs/Audits/Evidence/BP-04-Scheduling/README.md) distinguishes the initial Windows marker-sharing failure, bounded test-only repair and final passing run.
