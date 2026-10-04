# Campaign Research context selection

- Status: BP-07.03/B1.01a verified; Planning0.31/public Planning0.8.
- Owner: Planning immutable selection and request binding. Research owns records/assessment; Runtime owns campaign validation/execution.
- Design: [campaign context](../../../../../docs/Build%20Plans/BP-07/BP-07.03%20Physical%20design.md).

ResearchSelection.from_bytes/bind stores canonical bytes and the revalidated original RequestSnapshot. It accepts only campaign_proposal/supervision purposes, exact engagement/request hash, scoped unique question/need references and unique assessment identities. Distinct explicit revisions of one question remain distinct; authored selection ordering is retained. An assessment selects the complete original EvidenceAssessmentRequest plus expected status hash, not an invented mutable assessment revision.

SelectionPolicy checks each assessment's selected exact question, unique answer criteria/receipt identities and every referenced Artifact against an included original context entry. Omitted/foreign/changed Artifacts cannot become selected evidence by appearing inside assessment metadata. These checks do not establish current processing rights, record existence, question criteria meaning or an actual matching status digest. B1.01b owns record/read-set binding; B1.02 owns authenticated owner reads.

Limits:64 questions,64 needs,32 assessments and256KiB total canonical selection. Strict UTF-8 JSON rejects duplicate keys, nonfinite values, unknown wire fields and invalid scalars. DTOs are revalidated rather than trusted after model_copy. Returned DTOs cannot mutate the retained bytes. Empty selections remain explicit and confer no scientific context. No provider/network/filesystem/SQL calls, current-head lookup, acceptance authority or persisted registration belongs to this value boundary.

Tests are owned by tests/campaign_context; public wire tests by contracts/planning/tests/test_campaign_context.py. The fixture request is adapted from the existing local context fixture with campaign purpose/actions. Its exact request/selection digests establish canonical compatibility, not real-owner contact. Replacement preserves byte format, scoped identities, deliberate revision/order distinctions and explicit missing authority. No migration or historical schema change accompanies this additive selection root.

Verified 2026-10-04 17:18:21:111 source/111 independently installed cases;67 statements8 branches100%. [Evidence](../../../../../docs/Audits/Evidence/BP-07-Campaigns/Research_Selection.json). No persisted record/owner-contact claim.
