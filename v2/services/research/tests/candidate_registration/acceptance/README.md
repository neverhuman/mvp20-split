# Public operator to candidate handoff

- Owner: Research candidate registration, BP-08.03/B1.03b.ii; passed 2026-10-06 13:27:08 (America/Chicago).

dev/verify_candidate_handoff.py builds seven independent installed closures: Runtime, Data, Research, three synthetic operators and an SDK-only controller. The controller contains no peer-private implementation or SQL library. Each host receives only its SQL role and configured tokens; workers receive only their own worker token. No model credentials, migrations or fixture reset occur.

Each profile runs one public graph invocation with its distinct input schema. Actual workers read/write real Data Artifacts and Runtime accepts their completions. Independent expected values check numeric -1, polymer A/A with unknown metadata retained, and DNA AGGT. Research registers each accepted output Artifact as a proposed candidate and replays/readbacks the exact declaration. Runtime retention confirmations are checked independently.

Research restarts from the same installation, then Data restarts with only Research's read principal removed. Candidate registration retry must fail403 while historical candidate read remains exact. This is current-rights and process-restart evidence; independent replacement/images/Registry activation remain V1. Image identities in this fixture are explicitly declared pins, not built images or cluster deployment. Registration never proves molecular validity, synthesis feasibility or scientific fitness.

Output directories, SQL scopes, original and revoked Data configurations, tool schemas, graph definitions and evidence are retained. Host cleanup stops only owned processes. The existing owner SQL/API suite separately covers concurrency, atomic rollback, provenance and immutable grants.

Evidence: `.test-results/candidate-handoff-20261006a/http/evidence.json`; compact committed summary `docs/Audits/Evidence/BP-08-Search/Candidate_Handoff.json`. Three completed one-invocation graphs, three confirmed output reservations and three exact candidate declarations; 12 boundary checks11.52s.
