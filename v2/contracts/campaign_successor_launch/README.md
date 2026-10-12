# Successor launch public contracts

UI-01.08/P1, version0.1.0. Additive transport package; Deployment owns launch state
and workers, Runtime owns predecessor transfer and execution. Architecture:
../../docs/Architecture/System/System_Architecture.md.

`parse_successor_launch` accepts only `campaign.launch_successor` and nested
`graph.admit_draft_successor`. Both require explicit numeric command encoding.
Actor, scope and command ID must match across envelopes. The nested Runtime bytes
and digest survive canonical outer replay. Draft validation, predecessor cut and
carried-value digests remain explicit. Missing/rejected successor admission never
falls back to `graph.admit_draft` or the original fresh-launch route.

The separate receipt fixes `campaign-successor-launch.v1` and retains predecessor,
original command/hash, admission outcome and managed-worker progress. HTTP auth,
single-active-campaign policy, durable retries and owner acceptance belong to
Deployment; transport parsing grants none of those. Unknown admission stays
unresolved until exact receipt reconciliation. No database, process or service
implementation dependency belongs here. Existing LaunchRequest/LaunchReceipt
schemas remain unchanged.

Owned tests: tests/test_contract.py. Replacement acceptance: original nested hash,
old-family rejection, scope/actor/command mismatch, missing draft/predecessor/carry
pins, duplicate-key and raw size bounds. Runtime compatibility uses its published
draft-successor parser. Deployment implementation is a later P4 gate.
