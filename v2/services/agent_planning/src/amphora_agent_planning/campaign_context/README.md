# Campaign Research context selection

SQ-01/C2a adds explicit version2 FollowupSelection parsing only with the exact new
output profile. Existing version1 bytes and Research packet shape stay unchanged.
The focused campaign_followup module owns selected-criterion uniqueness, exact focus
Artifact selection and record membership. ResearchContext invokes that binding for
version2 only; absent target identity/assessment records reject instead of fabricating
membership. Unassessed targets may omit an assessment; weak/conflicting assessments
remain usable. Actual target serialization/provider execution integration is C2b.

- Status: BP-07.03/B1.01a verified; B1.01b selected-record projection verified. Planning0.32/public Planning0.8.
- Owner: Planning immutable selection and request binding. Research owns records/assessment; Runtime owns campaign validation/execution.
- Design: [campaign context](../../../../../docs/Build%20Plans/BP-07/BP-07.03%20Physical%20design.md).

ResearchSelection.from_bytes/bind stores canonical bytes and the revalidated original RequestSnapshot. It accepts only campaign_proposal/supervision purposes, exact engagement/request hash, scoped unique question/need references and unique assessment identities. Distinct explicit revisions of one question remain distinct; authored selection ordering is retained. An assessment selects the complete original EvidenceAssessmentRequest plus expected status hash, not an invented mutable assessment revision.

SelectionPolicy checks each assessment's selected exact question, unique answer criteria/receipt identities and every referenced Artifact against an included original context entry. Omitted/foreign/changed Artifacts cannot become selected evidence by appearing inside assessment metadata. These checks do not establish current processing rights, record existence, question criteria meaning or an actual matching status digest. B1.01b owns record/read-set binding; B1.02 owns authenticated owner reads.

Limits:64 questions,64 needs,32 assessments and256KiB total canonical selection. Strict UTF-8 JSON rejects duplicate keys, nonfinite values, unknown wire fields and invalid scalars. DTOs are revalidated rather than trusted after model_copy. Returned DTOs cannot mutate the retained bytes. Empty selections remain explicit and confer no scientific context. No provider/network/filesystem/SQL calls, current-head lookup, acceptance authority or persisted registration belongs to this value boundary.

Tests are owned by tests/campaign_context; public wire tests by contracts/planning/tests/test_campaign_context.py. The fixture request is adapted from the existing local context fixture with campaign purpose/actions. Its exact request/selection digests establish canonical compatibility, not real-owner contact. Replacement preserves byte format, scoped identities, deliberate revision/order distinctions and explicit missing authority. No migration or historical schema change accompanies this additive selection root.

Verified 2026-10-04 17:18:21:111 source/111 independently installed cases;67 statements8 branches100%. [Evidence](../../../../../docs/Audits/Evidence/BP-07-Campaigns/Research_Selection.json). No persisted record/owner-contact claim.


## Selected records and relevance

ResearchIdentity binds a closed question/need/assessment identity from existing public DTOs. ResearchRecord stores revalidated immutable body bytes and digest. ResearchContext.bind revalidates its original selection, admits only selected records once, orders retained records by authored selection, and adds explicit gaps for every missing input. Supplied denied/unavailable gaps cannot alias a supplied record or unselected identity. Pending/failed assessment responses become gaps; completed statuses must match the expected digest and original request/actor relationships.

ResearchRecordPolicy validates public scope, predecessor and criterion/need relationships without recomputing scientific evaluation. Missing selected questions/needs produce explicit dependency findings while other records survive. Unselected dependency references stay visible; they do not silently become selected context. Contradicted/unknown/supported, answered/sufficient and scientific authority are retained exactly. Assessment evidence references must bind its original receipt selection. Pure factories do not prove Research contact or current source rights.

The private packet format is planning-campaign-research-context.v1 with selected_metadata_only authority. Each record is at most1MiB; total input record bytes and final packet are at most4MiB. Question/need/assessment counts remain64/64/32. Oversized records fail explicitly; nothing is silently truncated. ResearchGap owns finite unavailable reasons. Returned records and canonical projections retain no caller-mutable DTOs. Use the validated factories at boundaries; direct dataclass construction is internal, not proof of provenance.

ResearchReadSet binds each selected available record digest or explicit absence. changes(observed) reports changed/missing original identities and ignores extra unrelated records. It performs no latest lookup, repinning, source read, active-campaign invalidation or execution acceptance. Later proposal policy chooses the relevant selected dependencies; this object only compares supplied observations. Tests retain weak evidence, exercise appearance/disappearance and show unrelated selected records cannot invalidate an existing read set. No scientific sufficiency is inferred from a zero-change comparison.

Verified 2026-10-04 17:28:41:64 focused/143 independently installed cases;269 statements44 branches100% across this module. [Record evidence](../../../../../docs/Audits/Evidence/BP-07-Campaigns/Research_Context_Records.json). Actual owner contact remains the next boundary.
