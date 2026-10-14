# POP-01 History

Canonical state: [parent](POP-01%20Population%20Campaign%20Execution%20and%20Experience.md)
and [Execution tracker](POP-01.01%20Population%20Execution.md). This file is history,
not a second completion tracker.

## 2026-10-13 20:28:22 ? E1 specification and membership foundation

Owner approved POP-01.04 at2026-10-13 18:45:57. Temporary remote-access interruption
resolved when owner opened a fresh invitation; confirmed working. Both demo wrappers
local13k/LAN13i drained before source changes; frozen servingh remains unchanged.

contracts/population0.1 introduces independent specification, membership-page and
membership-manifest roots. Search0.6 adds pure OriginalPopulation and
GenerationMembership without changing existing numerical worker operations or
algorithms. No0.6 Registry/Runtime deployment claimed. Public core/tools/search
values are reused; no private service imports or I/O in domain objects.

Verification: initial72 specification/legacy checks, then54 page checks. Stronger
page-byte test initially failed because its fixture fit within131072bytes; corrected
to exercise UTF-8 byte length separately from character count. Final scoped suite:
209passed92.57s, Search excluding workspace-only reuse audit plus new contracts and
publication.678schemas published;672predecessor bytes pinned. Exact specification
canonical bytes and domain-prefixed digest checked against an independent .NET hash.
Dependency guard passed. Dev/owner/new-contract uv locks refreshed offline.

Independent two-wheel-install Search proof passed2026-10-13 20:30:36 at
`.test-results/pop01-e1-installations-20261013a`:227tests in each installation, identical
wheel closure and legacy checkpoint/RNG replay. [Compact evidence](../Audits/Evidence/POP-01/Specification_Membership.json).
Next E1/D1: candidate birth, evaluation/outcome, fitness, selection, successor and
material lineage. Source-level membership verification is not proof of Artifact
rights/retention, birth content, Registry eligibility or accepted predecessor history.
No paid calls, scientific-validity claim or scale benchmark.
