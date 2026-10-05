# Supervisor journal

Implementation: private immutable frames and bounded series under BP-07.04/B1.03a; persistence, leases, transports and decision acceptance are not implemented here.

`RequestFrame.capture` binds the public supervisor request to original byte-owned Runtime observations and the configured Planning actor. It records the separate preparing Runtime actor. `from_bytes` revalidates the private `runtime-supervision-request-frame.v1` profile, canonical JSON/base64 and all existing request/observation hashes. Limits: 16 MiB per frame, existing 256 KiB request, 256 observations, 1 MiB per observation and 8 MiB combined state/output. Returned documents are fresh projections; bytes own retained state.

`RequestSeries` validates 1–16 immutable frames with exact root/parent hashes, unique Planning engagements, unchanged decision/checkpoint/actors/footprint and nondecreasing Runtime cuts. Context bindings stay fixed; call ceilings, action set and deadline cannot widen. Required entries persist except the prior declaration constraint identified by the original declaration digest. That exception does not authorize a broader declaration; admitted policy validation belongs to B2.

No database/network effects, signatures, source-rights decisions, provider ledger, scientific authority or graph mutation. Received frames cannot prove actual stored node membership, active ancestors or absence of a materialized worker activation. The future SQL producer must rederive those facts under the run lock using configured principals. Future-only receipt corrections remain unchanged.

Dependencies are public supervision contracts and local scope/request objects. Tests live in `tests/supervision_journal`; replacement must preserve exact original bytes/hashes and rejection behavior. Future private profiles need retained readers. SQL migration and independent persisted-history cutover remain B1.03b–d.
