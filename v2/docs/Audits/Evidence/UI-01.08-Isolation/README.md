# UI-01.08e schema isolation and repair audit

- Status: isolation/repair complete100%; full campaign acceptance pending.
- Reviewed: 2026-10-12 18:39:10 America/Chicago.
- Verification:97 focused tests pass16.28s; independent Planning0.133.0 installation;
  eight prior envelopes/acceptance outcomes replay unchanged.
- Result: installed v6 schema exactly equals passing full-schema probe.

| Case | Result |
|---|---|
| tiny strict boolean | Pass |
| reachable abstention | Pass |
| structure | Invalid probe HTTP400; removed property named minimum accidentally |
| full schema without regexes | Empty output, explicit zero usage, max_output_tokens |
| corrected structure-v2 | Pass |
| full schema without numeric constraints | Pass |
| full schema without only NumberConstant.value +/-1e100 bounds | Pass |
| tiny number schema with +/-1e100 bounds | Empty output, explicit zero usage, max_output_tokens |

Same pinned model/direct transport, synthetic input, reasoning none,512 output
and fresh process per case. Eight originals reserve$0.24 of self-imposed16/$0.48.
Stopped on isolation. Reported token estimate$0.012626250, not invoice; HTTP400
has no usage. No refund/reset. Triggering fragment isolated, not provider internals,
exact failing threshold or which bound independently triggers failure. Passing
full-schema probes produce abstention, not a campaign graph.

## Scoped drift review

Planning0.133.0 adds v6/fit.v8: omit exactly minimum/maximum on NumberConstant.value
from generation. Retain local numeric range/finite constraints, all other generation
constraints, public contracts, prompt content, model and transport. Tests reject
out-of-range values. Old versions and all8 originals unchanged; distinct schema
identity prevents silent replay mutation. Isolated package excludes peer services.

Probe traversal fault repaired with schema-aware handling and regression test;
faulty original retained and excluded from causal inference. No credentials,
reasoning text or arbitrary remote error prose retained. No serving change.

Next: full supported campaign original through compilation/successor, then P5.4.
Campaign aggregate10/$2.55 exhausted; diagnostic authority does not admit campaigns.
No new allowance implemented. Parent progress unchanged.

summary.json owns case outcomes/IDs/accounting; folders retain exact requests,
reservations, safe diagnostics and visible output. installed-material.json holds
8 replay digests and repaired schema; installation.json pins built wheels.
manifest.json hashes all evidence except itself.

2026-10-12 18:39:53: production dependency boundary check passes (boundaries.txt).
