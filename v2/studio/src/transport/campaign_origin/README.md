# Campaign provenance transport

Owner: Studio, UI-01.07/P3. User: research SME inspecting why a saved campaign
was proposed. Public boundary: Planning campaign-origins GET with exact draft pins.
No keys, writes, provider calls or latest-head lookup.256KiB success/4KiB error
bounds, timeout/cancellation, and a strict named missing-origin response distinguish
no recorded association from an unavailable endpoint.403 never becomes absence.

Generated planning.campaign-origin-knowledge/v1 validators preserve owner schema
identity. `verifyOrigin` checks the body digest, scope, draft/save receipt relation,
Research selection membership/completeness and Knowledge graph pins. It does not
verify a provider signature, infer scientific confidence or grant content rights.
Runtime receipt/draft and Research record checks belong to the owning page model.
Raw prompts and private preparation packets never enter this transport.

349 Studio tests pass; scripted browser failures/absence and responsive rendering
pass. Client line/branch95.06/80%, identity73.58/90.48%; Knowledge branches and some
cancellation paths remain unexercised. Actual-owner qualification is recorded below. Rebuild must
preserve bounded failure, cancellation, exact identity and truthful absence semantics.

2026-10-11 19:26:42: P4 actual deterministic Planning compiler -> Runtime saved draft
-> browser launch/results -> exact origin/Research/consumed Knowledge passes on
localhost and LAN at1440/390. Manual draft absence and altered pins are explicit.
Screenshots inspected; no serious/critical axe findings. See UI-01.07 audit for
retained failures and limits; no live-model or scientific-validity claim.
