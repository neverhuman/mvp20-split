# Documentation Debt

- Status: active dashboard
- Last refreshed: `2026-10-06 10:29:13` (America/Chicago)
- Scope: summaries and decomposition needed to keep agent context bounded
- Next step: address entries when their owning work becomes active

| ID | Symptom | Owner document | Needed work | Priority / trigger |
|---|---|---|---|---|
| DOC-001 | Product Requirements remains long; domain contracts and section ownership map now provide focused navigation | Architecture/Requirements/Product_Requirements.md | Preserve product authority; introduce stable requirement IDs when detailed implementation traceability needs them | During implementation-plan breakdown; nonblocking for completed architecture decomposition |
| DOC-002 | Historical coatings/MVP implementation and remediation documents coexist with current graph-native direction | Architecture/README.md | Mark relevant reference scope and audit/rebaseline inherited proposals before activation | When an inherited proposal is selected for planning |
| DOC-003 | Repeated narrow acceptance changes require reading the growing independent_builds orchestrator | dev/README.md and dev/verify_foundation.py | Split dependency-closure/install preparation from owner-specific acceptance adapters; retain the one-command gate, environment isolation and honest evidence tiers | BP-03.04 adds replica acceptance, or the next primary service adds another process harness; nonblocking for .03 |

| DOC-004 | Root Runtime/Data READMEs contain long chronological checkpoints and stale current-summary statements, causing broad reads for narrow integration questions | services/campaign_runtime/README.md; services/data_artifacts/README.md | Keep current package/API/owner summary and module index at top; move durable checkpoint prose to companion history; preserve focused rebuild contracts | Next touch of each root README; nonblocking for BP-08.02, use owning modules and current manifests meanwhile |
