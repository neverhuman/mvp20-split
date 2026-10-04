# Feedback record reader

Implemented: bounded, read-only Research assessment/publication and historical receipt correction reads; Knowledge proposal status and accepted-change reads. Python-published schemas remain authoritative; Studio generates nine derivative roots under `contracts/generated/feedback`.

`FeedbackClient` uses the shared same-origin scientific transport with fixed routes, body/response limits, cancellation and deadlines. It holds no credentials, persistence or owner policy. It cannot submit assessments, publish receipts, correct evidence, accept proposals or repin campaigns. Explicit historical receipt selection is mandatory; null/head discovery is rejected before fetching.

Read results must match selected request, scope and immutable identity. Completed assessment request/actor must match the enclosing record. Pending, failed, insufficient, rejected and abstained results remain distinct data. Structural Knowledge acceptance and synthetic Research sufficiency never assert scientific certainty.

Proposal and accepted-change fingerprints use the owner's sorted compact UTF-8 JSON; correction records use sorted compact ASCII-escaped JSON. Correction reads validate chain, ordinal, predecessor and supersession-notice relationships, source/effective receipt scope, purpose, subject and outcome. Hash validity alone does not authorize a scientifically meaningful claim. Current access rights remain owner-controlled.

Dependencies: generated public schemas, scientific HTTP/identity helpers and provenance SHA-256/cancellation helpers. No private owner implementation imports. `tests/transport/feedback.test.ts` owns boundary tests including Python golden hashes, stale/wrong scope, malformed replies, denial, explicit revisions and weak outcomes. Independent `dev/verify_studio.py` copies all public schema pins and installs Studio separately. Actual-owner integration and visible lineage are subsequent BP-06.06/B2.03 deliveries; no deployed gateway or browser identity selection is provided here.

Replacement must retain exact selections, safe routes, owner fingerprint encodings, qualified outcome semantics and rejection of implicit repinning. Existing shared transport tests cover streamed deadlines, body limits and cancellation. Current scoped coverage: client and correction lines100%, branches97.30%/95.24%; defensive invalid runtime owner value and non-ASCII correction encoding callback are not directly exercised.
