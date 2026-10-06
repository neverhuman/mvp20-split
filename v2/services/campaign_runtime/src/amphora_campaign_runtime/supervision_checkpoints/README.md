# Concrete supervision checkpoints

Runtime owns immutable checkpoint identity and original selected observations for one concrete graph activation. Design: [admitted checkpoint policy](../../../../../docs/Build%20Plans/BP-07/BP-07.04%20Admitted%20checkpoint%20policy.md), B2.01c.iii.

`CheckpointSeed.capture(policy, footprint)` verifies the exact admitted policy, authored rule, target fields and read selection. The record preserves observation state/output bytes using the existing journal observation codec; reconstruction rederives snapshot digests and rejects noncanonical bytes. Identity includes scope, run, plan, policy, rule and concrete activation, so global progress or a refreshed observation cannot invent a new decision slot for that occurrence.

This initial pure boundary creates no SQL record, request, provider grant or execution effect. Transaction-local storage and coordinator integration follow. Planning context preparation and model execution remain separate; a seed is not a public Planning request. B2.02 owns terminal winners and scalar effects. No scientific validity claim follows from a checkpoint.

Dependencies are Runtime policy/scope objects, the existing observation codec and public snapshot DTOs. Replacement tests belong to tests/supervision_checkpoints and must preserve exact bytes, identity across irrelevant progress and policy/read-selection rejection. Public predecessor profiles remain unchanged.
