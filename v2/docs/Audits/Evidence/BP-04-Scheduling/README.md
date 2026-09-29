# BP-04 scheduling evidence

- Owner: [BP-04.02](../../../Build%20Plans/BP-04/Completed/BP-04.02%20Frontier%20and%20scheduling.md).
- Reviewed: `2026-09-28 19:30:50` (America/Chicago).

[B3.json](B3.json), pinned by [B3.sha256](B3.sha256), preserves eight actual coordinator-process cases over the owned PostgreSQL fixture: same/distinct command races with two observed lock waiters, death after commit before reply, empty scatter, changed loop feedback/predicate termination, iteration limit, budget exhaustion and independent branch progress. The production implementation is Runtime 0.4.0 from commit dd325fe. Expected activation identities/frontiers are independently constructed in the owner tests.

The complete owned scheduling suite passed 60 cases. Logs remain `.test-results/bp0402-b3-scheduling.log`; source scenario contract is [scheduling verification](../../../../services/campaign_runtime/tests/scheduling/README.md). These processes use the editable owner package and actual database; their tool completions use a scripted artifact-reservation peer. They do not replace V1 independent package installation, actual public graph/tool/Artifact integration or replacement proof. Existing B2 foundation evidence (799 tests, thirteen independent installs, REC-01..09) remains distinct from graph-specific peer acceptance.

[V1.json](V1.json), pinned by [V1.sha256](V1.sha256), preserves eight actual independently installed graph/Registry/Runtime/Artifact/SDK/tool and fresh Runtime replacement scenarios, scope bab36cf644df43e59a370437d68c94d1. Thirteen wheel hashes match the public closure, including the separately verified scientific tool image bytes. Outputs, Artifact predicates, iterations, empty/parallel scatter, reverse completion/lost reply, retained history, installed polling and seven Artifact confirmations pass. Log .test-results/bp0402-v1-graphs-final.log. [Scheduling closeout](../../BP-04.02_Scheduling_Closeout.md) records scope and limitations.
