# <Focused Architecture Responsibility>

- Document role: intended design; not a code-module README
- Design maturity: proposed | reviewed | needs decision
- Last reviewed: YYYY-MM-DD HH:mm:ss (America/Chicago)
- Parent: <immediate architectural owner>
- Requirement/design basis: <precise source references>
- Vocabulary status: <proposed logical names versus implemented contracts>

## Responsibility and Boundary

Owns/does not own; inputs, outputs and adjacent contract owners. Explain the design choice rather than repeating requirement wording.

## Components and Domain Objects

Component responsibilities, authoritative records and behavior, stable identity/revision relationships. Distinguish authoritative state, scratch state and derived projections. Do not invent database/API technology where it is undecided.

## Lifecycle and Interaction Protocol

Commands, preconditions, state transitions, read/write ownership, acceptance/commit boundary and resulting events or artifacts. Include concurrency and permission checks where they affect correctness. Use a diagram when it clarifies the protocol.

## Failure and Recovery

At least one concrete failure scenario with resulting disposition and recovery path. Cover retries, stale inputs, uncertainty, authority, partial effects and replay as relevant; do not merely list failure keywords.

## Verification and Remaining Decisions

Observable invariants, representative boundary cases, validation evidence needed and explicitly unresolved decisions. Link supporting detail; create narrower child contracts when responsibilities become independently complex. Keep implementation facts in the corresponding code-module README once it exists.
