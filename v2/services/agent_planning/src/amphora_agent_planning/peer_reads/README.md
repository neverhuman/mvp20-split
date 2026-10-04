# Planning bounded peer reads

- Status: BP-07.02/B2.02a.ii verified against both installed owners.
- Owner: Planning transport behavior only; no peer business policy or state.

ReadProfile is a compiled, immutable catalog of allowed POST read paths, public request/response DTOs and resource ceilings for Knowledge or Research. Models and incoming requests cannot select routes, owner profiles, credentials or Python handlers. BoundedReadTransport accepts only explicit authenticated127.0.0.1 HTTP endpoints, strict JSON records and profile-bound ReadWindows. No redirects, proxies, automatic retries, writes or SQL are provided.

ReadWindow accounts whole-review wall-clock, call count and aggregate bytes. Per-route response caps and trusted per-profile request caps bound each exchange; existing profiles keep4KiB requests. Campaign Research uses256KiB requests and160 calls for complete selected assessment requests; socket shutdown timers bound trickling headers/bodies. Stable owner-prefixed errors contain no peer bodies or secrets. Parsing and post-read checks must complete before a usable record is returned. Knowledge's predecessor limits/error codes remain unchanged; Research selects its own smaller closed catalog.

Public owner records still need semantic identity/scope binding in their owning reader module. This transport does not establish scientific truth, graph acceptance, source rights or durable leases. Tests stay with knowledge_access and research_access caller behavior; common boundary tests belong under tests/peer_reads when needed. Replacement must pass both callers' deadline, protocol, denial and exact-body cases.

Verified 2026-10-04 07:31:11:70 focused cases,212 shared/read statements28 branches98%;560 regression and542 independent tests. Actual public read proofs passed with8 isolated Planning workers and2 owner hosts per owner. Remaining coverage gaps are defensive socket cleanup and alternate empty-read paths. No migration or scientific acceptance claim.

BP-07.03/B1.02a.i extends only compiled profile configuration; the original Knowledge and extraction Research routes/deadlines/call counts remain unchanged. No persisted format or public DTO changes. Tests for the new profile live under campaign_research_access alongside the legacy caller transport suites.

BP-07.03/B1.02a.ii permits four compiled Research-only named exploration paths; the separate32-call view profile leaves legacy route tables unchanged. See research_view_access for exact page/scope/schema binding and explicit continuation.
