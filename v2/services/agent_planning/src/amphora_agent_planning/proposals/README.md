# Planning graph proposal validation

- Status: BP-07.02/B2.01b verified; B2.01c public owner reads next.
- Owner: Agent Planning; Knowledge alone accepts edits and owns graph history.
- Implemented: immutable pinned Knowledge context, source/identity/context candidate validation and bounded proposal construction. Actual public owner reads are B2.01c; submission/replay is B2.03.

KnowledgeContext binds the task's exact graph/head/vocabulary/policy/schema references to validated public GraphAuthoringProfile and DomainGraphSnapshot records. It independently verifies canonical snapshot/vocabulary hashes and basic record/alias consistency. Byte-owned records prevent a caller from mutating a retained context through DTO containers. GraphFacts is a fresh per-validation lookup projection, never a shared state repository. It distinguishes historical identity, latest revision, aliases and tombstones. Labels preserve case; scientific identifiers such as Co and CO must not be collapsed by generic case folding.

This pure binding proves internal consistency, not that the Knowledge service was contacted. The later public reader must establish origin and exact historical snapshot readback. It must not silently rebase to a newer head. Context metadata is bounded256KiB for a profile and16MiB for a snapshot; exceeding a bound is explicit unavailability, never truncation. No provider, peer HTTP, SQL, graph acceptance or scientific entailment belongs in these pure objects.

Candidate validation retains item-specific findings and withhold structurally invalid operations and their dependents while preserving unrelated defensible proposals. Exact quotation bytes are a separate check from semantic meaning; inferred/weak/contradictory science is not a global campaign failure. Replacement must preserve scope, source/trace identity, edit targets, deterministic proposed IDs, explicit unknown context and Knowledge-owned acceptance.

## Public inputs and output

ProposalInputs.from_publication rebinds the task, captured observation, source review, pure Knowledge context and finalized publication receipt. It reconstructs the interpretation payload and compares its candidate hash and attribution projection against the observed bytes. These are private domain inputs; later workflow integration must load the owned journal and public peer records, not accept caller claims of publication.

GraphCandidateValidator.validate returns byte-owned proposal content plus item findings, withheld paths and proposed/partial/unresolved/abstained posture. Deterministic IDs bind the task and candidate local identity; a proposal identity additionally binds candidate and published interpretation bytes. Replacements reserve their candidate before validation, so failed corrections never fall back to additions. Selected prior revisions must be exact, current within the pinned historical snapshot and non-retracted/unmerged where required. Explicit context edits retain entity name/type. Aliases retain historical records; case-sensitive NFC labels avoid accidental scientific identity conflation.

Existing matches can reuse their owner context; new entities and assertions require explicitly selected context. Legacy v1 entities use the task's explicit applicability reference, never a scientific default. Inferred assertions cannot acquire reported posture. Exact quotation checks do not prove a statement follows from the quote. Contradictions and unknown confidence remain visible through the interpretation and findings. Proposal bounds are128 operations,64 unique source spans/conversion traces and256KiB canonical bytes; overflow is explicit and never truncated. Research candidates and repair orchestration remain subsequent gates.

Tests live under tests/proposals with independent operation/findings expectations, scripted public records and publication receipts. Actual Knowledge origin proof is not claimed by those fixtures. This module performs no I/O and stores no durable state.

Verified 2026-10-04 06:28:33:36 pure cases;483 source/contract/dev,465 independently installed cases and20 process stages. Pure module coverage409 statements116 branches at98%; remaining defensive error/selection and alternate history branches. No peer implementation is present in the independent Planning installation.
