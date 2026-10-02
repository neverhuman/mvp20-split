# Accepted Change Replay

- Status: BP-06.02 B1-B3 implemented; independent installed replacement accepted (169 initial / 39 replacement tests).
- Owner: Knowledge; [replay architecture](../../../../../docs/Architecture/Knowledge/Authoring.md).

AcceptedEdit.review combines a prior GraphState/head, typed proposal, adapter-supplied actor and exact ReferenceValidation observation. The observation must contain precisely the collected public inputs and cannot be dated after acceptance. It computes the immutable semantic result, then builds AcceptedChangeContent and hashes that content into AcceptedChangeRef. A complete DomainHead binds the resulting snapshot and accepted change. Incidental review time changes the log fingerprint but not the semantic snapshot.

This is an owner-private factory, not an authorization endpoint. A caller-supplied observation is not proof that peers were contacted. The authenticated transport/validation/persistence siblings issue observations from real scoped Data/Research reads, bind actor/policy from trusted configuration and persist proposal/decision/log/snapshot/head atomically. Tests explicitly use synthetic observations. No scientific adjudication occurs; authority is structural_only.

GraphReplay rebuilds from genesis under pinned vocabulary/policy, consuming at most the configured1..10000 records. It requires exact graph, unique change IDs, consecutive positions, content hashes and policy. It reapplies accepted typed operations and requires complete regenerated accepted records/heads to match. Missing, reordered, duplicate, altered or substituted history fails; no entry is silently skipped. Replay performs no I/O and never calls an LLM, reinterprets prose or retroactively reruns current peer rights against historical metadata.

The returned ReplayedGraph is a candidate in memory. It does not publish a head, prove current payload rights, or authorize an active campaign to adopt a revision. Transactional persistence is implemented in the sibling persistence module; private build/catch-up/CAS publication is implemented by the sibling rebuild module. Public rebuild operations read the owner's accepted ledger, never trust client-submitted accepted records on the strength of hashes alone.

Tests independently assert preserved assertion revisions, negation, Research links and tombstones, exact incremental/replay equality, damaged histories, bounded replay and timestamp/hash separation. Authentication and actual peer validation are verified in separate owner suites. Mid-build process interruption is verified in the separate acceptance suite; independent installed replacement accepted (169 initial / 39 replacement tests).

GraphReplay.cursor() creates an owner-private ReplayCursor from genesis. append validates the next accepted record; through consumes an exact bounded tail to a complete DomainHead watermark. It rejects missing/extra entries, foreign heads, hash substitution, regression and duplicate change IDs across rounds. Cursor state is immutable: failed catch-up cannot mutate the prior verified prefix. This is not a public snapshot import API and performs no durable publication.

Verification:18 pure replay/cursor tests prove ordered history and exact catch-up semantics. Durable publication, process interruption and replacement evidence belong to their owning suites and the service README.
