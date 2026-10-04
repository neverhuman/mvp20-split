# Planning Research proposals

- Status: BP-07.02/B2.02a verified; research_access supplies authenticated owner-read binding.
- Owner: Agent Planning; Research owns declarations/assessment, Data owns published answer Artifacts.
- Inputs: exact PublishedCandidate and immutable selected QuestionContext. No Knowledge snapshot is required by this module.

QuestionContext binds exact public ResearchQuestion records to task-selected references and validates scope, unique criteria and predecessor shape. It owns bytes rather than caller-mutable DTOs. Missing selected records remain unavailable; their dependent items cannot be resolved by guessing. This pure context does not prove Research was contacted; research_access owns authenticated public read binding. Explicit read gaps remain context findings without withholding unrelated proposals.

ResearchProposalValidator resolves questions first, then candidate answers and evidence needs. Duplicate local IDs withhold every conflicting candidate. A target is exactly one local proposed question or selected owner reference. Missing/ambiguous questions withhold dependents while unrelated useful proposals proceed. New question/need IDs derive from task identity, kind and local key. Context must be explicitly selected, methods explicitly supplied, and need criteria a unique subset of the exact target question. Method references are declarations, not verified capabilities or permission to run tools.

The additive public planning.research-proposal-set/v1 bundle carries proposed question/need records, candidate answers, model attribution, byte-verified grounding, originating candidate paths and item findings. Authority is proposal_only and validation quotation_and_structure_only. It never labels answers accepted or source-stated semantics proven. Local question references are provisional until Research registers them; downstream submission must obtain owner receipts before treating those identities as accepted. Current Research HTTP has declaration reads but no declaration-write endpoint; B2.03 owns that integration gap.

PublishedCandidate is the shared provenance object in publication/candidate.py. It rebinds the exact observed draft, source bundle and finalized interpretation payload/receipt. Graph ProposalInputs composes this object with Knowledge facts; Research validation does not acquire graph context to verify source provenance. No private owner imports, SQL, network or publication effect belongs here.

Each group is bounded32 candidates. The canonical output cap is256KiB; overflow retains explicit per-item findings and emits no silently truncated partial batch. Quality/contradiction alone is not a veto. Unresolved and abstained outputs remain useful for future campaigns. Tests belong under tests/research_proposals, contract tests under contracts/planning/tests; aggregate repair admission and actual owner handoff are subsequent ordered gates.

Verified 2026-10-04 07:07:14:20 pure Research cases plus36 shared graph binding cases,7 new strict wire cases;542 regression,524 independently installed tests20 process stages. Changed modules206 statements28 branches96%; remaining defensive oversized-bundle fallback.506 schemas preserve504 predecessor files; no DDL or historical-byte change.
