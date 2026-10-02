# Accepted Change Replay

- Status: BP-06.02/B1 pure structural review/replay implemented; private durable accepted ledger implemented; public peer validation pending.
- Owner: Knowledge; [replay architecture](../../../../../docs/Architecture/Knowledge/Authoring.md).

AcceptedEdit.review combines a prior GraphState/head, typed proposal, adapter-supplied actor and exact ReferenceValidation observation. The observation must contain precisely the collected public inputs and cannot be dated after acceptance. It computes the immutable semantic result, then builds AcceptedChangeContent and hashes that content into AcceptedChangeRef. A complete DomainHead binds the resulting snapshot and accepted change. Incidental review time changes the log fingerprint but not the semantic snapshot.

This is an owner-private factory, not an authorization endpoint. A caller-supplied observation is not proof that peers were contacted. The forthcoming authenticated adapter must issue observations from real scoped Data/Research reads, bind actor/policy from trusted configuration and persist proposal/decision/log/snapshot/head atomically. Tests explicitly use synthetic observations. No scientific adjudication occurs; authority is structural_only.

GraphReplay rebuilds from genesis under pinned vocabulary/policy, consuming at most the configured1..10000 records. It requires exact graph, unique change IDs, consecutive positions, content hashes and policy. It reapplies accepted typed operations and requires complete regenerated accepted records/heads to match. Missing, reordered, duplicate, altered or substituted history fails; no entry is silently skipped. Replay performs no I/O and never calls an LLM, reinterprets prose or retroactively reruns current peer rights against historical metadata.

The returned ReplayedGraph is a candidate in memory. It does not publish a head, prove current payload rights, or authorize an active campaign to adopt a revision. Transactional persistence is implemented in the sibling persistence module; private build/catch-up/CAS publication remains B2. Future public rebuild operations must read the owner's accepted ledger, never trust client-submitted accepted records on the strength of hashes alone.

Tests independently assert preserved assertion revisions, negation, Research links and tombstones, exact incremental/replay equality, damaged histories, bounded replay and timestamp/hash separation. Authentication, actual peer validation, process interruption and replacement are separate forthcoming gates.

Earlier pure-module checkpoint:36 owner tests and36 independent installed-owner tests pass;26 authoring and10 replay cases. Combined measured coverage319/334 statements and124/140 branches; remaining defensive error branches are listed in the committed Domain_Replay evidence. No transaction or scientific-authority coverage is inferred from this pure suite.
