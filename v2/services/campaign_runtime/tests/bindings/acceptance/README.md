# Installed binding acceptance

Owner: Campaign Runtime, BP-04.04A/V1. Run `dev/verify_graphs.py --profile bindings --images <verified image manifest>` with the labeled PostgreSQL fixture explicitly enabled. This gate independently installs Runtime (including a fresh replacement), Artifact, registry, SDK and synthetic tools; the controller runs inside the isolated SDK interpreter and uses public owner HTTP only.

The authored dynamic graph comes from the binding suite's `definitions.py`. Ordinary installed numeric workers execute producer, candidate scoring and consumer invocations. Arithmetic expectations are independently evaluated from each public input, with final values [7,11,15] after two generations. There is no batch-tool substitute for graph-controlled scatter, gather or feedback.

`relay.py` forwards actual Artifact operations and captures scoped public receipts without bearer tokens. Its explicit barrier holds one successful Artifact finalization response while the Runtime process is terminated and replaced. The fresh owner must recover the original publication without another stream, then preserve committed graph observations and public retention proofs across later replacement. Process contention and deadline/cancellation cases remain the separate B3 suite.

Evidence is written under `.test-results/binding-acceptance/<scope>/`. Windows wheel/process execution and the separately verified Linux tool image profile are distinct evidence tiers; this does not establish target-host or scientific validity. Acceptance status and measured coverage belong to the canonical child tracker.
