# Draft successor transport

BP-08.04/B2.02; package0.1.0. Owner-approved additive execution boundary.

AdmitDraftSuccessor composes existing SuccessorProposal fields with exact
DraftSelection. parse_draft_successor accepts only graph.admit_draft_successor,
uses the existing versioned numeric canonical-command profile, rejects duplicate
carried targets and foreign fresh-input Artifacts. DTOs and parsing grant no
execution authority. Runtime authenticates actors, resolves current draft and
Registry eligibility, verifies predecessor readiness and commits all effects.

This separate public package preserves graph-runtime0.13 and every existing
schema/command byte profile. It has no SQL, network, domain transitions or peer
implementation imports. Rebuild acceptance requires owned tests, all630 frozen
predecessor schema hashes, numeric/identity rejection and unchanged older command
replay. Runtime integration tests own atomicity, head/cut races and replacement.
