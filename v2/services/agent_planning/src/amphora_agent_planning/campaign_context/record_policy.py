"""Public record coherence; scientific verdicts remain opaque owner observations."""

from ..context.policy import require
from .records import ContextFinding, ResearchIdentity


def predecessor(reference, previous, field):
    require((previous is None and reference.revision == 1) or
            (previous is not None and previous.scope == reference.scope and
             getattr(previous, field) == getattr(reference, field) and previous.revision + 1 == reference.revision),
            "campaign_record_predecessor")


class ResearchRecordPolicy:
    @staticmethod
    def question(record):
        require(record.applicability.scope == record.reference.scope, "campaign_record_scope")
        criteria = [item.criterion_id for item in record.criteria]
        require(len(set(criteria)) == len(criteria), "campaign_record_duplicate_criterion")
        predecessor(record.reference, record.supersedes, "question_id")

    @staticmethod
    def need(record, questions, selected_questions):
        require(record.question.scope == record.reference.scope == record.required_context.scope, "campaign_record_scope")
        require(len(set(record.criterion_ids)) == len(record.criterion_ids), "campaign_record_duplicate_criterion")
        predecessor(record.reference, record.supersedes, "need_id")
        identity = ResearchIdentity.bind("need", record.reference)
        question = questions.get(record.question)
        if question is None:
            return (ContextFinding(identity, "question_unavailable" if record.question in selected_questions else
                                   "question_not_selected"),)
        require(set(record.criterion_ids) <= {item.criterion_id for item in question.criteria}, "campaign_record_unknown_criterion")
        return ()

    @staticmethod
    def assessment(status, expected, questions, needs, selected_needs):
        require(status.request == expected.request, "campaign_assessment_request")
        assessment = status.outcome.assessment
        scope = status.request.question.scope
        require(assessment.request == status.request and assessment.actor_id == status.actor_id, "campaign_assessment_origin")
        require(assessment.subject.scope == scope, "campaign_record_scope")
        identity = ResearchIdentity.bind("assessment", status.request)
        findings, seen = [], set()
        question = questions.get(status.request.question)
        if question is None:
            findings.append(ContextFinding(identity, "question_unavailable"))
        for decision in assessment.needs:
            require(decision.need.scope == scope, "campaign_record_scope")
            key = (decision.need, decision.criterion_id)
            require(key not in seen, "campaign_assessment_duplicate_need")
            seen.add(key)
            if question is not None:
                require(decision.criterion_id in {item.criterion_id for item in question.criteria},
                        "campaign_record_unknown_criterion")
            need = needs.get(decision.need)
            if need is None:
                reason = "need_unavailable" if decision.need in selected_needs else "need_not_selected"
                findings.append(ContextFinding(identity, reason))
            else:
                require(need.question == status.request.question and decision.criterion_id in need.criterion_ids,
                        "campaign_assessment_need_binding")
            gap = decision.gap
            require(gap is None or (gap.need == decision.need and gap.criterion_id == decision.criterion_id),
                    "campaign_assessment_gap_binding")
            require(all(ref in status.request.receipts for ref in (*decision.supporting, *decision.contradicting)),
                    "campaign_assessment_receipt_binding")
        require(all(item.receipt in status.request.receipts for item in assessment.reviews),
                "campaign_assessment_receipt_binding")
        # Preserve supported/contradicted/unknown and answered/sufficient exactly;
        # neither these flags nor this consistency check establishes science.
        return tuple(dict.fromkeys(findings))
