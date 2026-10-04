import pytest
from amphora_agent_planning.research_access import QuestionReader
from amphora_agent_planning.research_proposals import ResearchProposalValidator

from ..research_proposals.support import ResearchCase


class Peer:
    def __init__(self, values):
        self.values, self.calls = values, []

    def read(self, path, reference, window):
        window.start()
        self.calls.append((path, reference))
        value = self.values[reference.question_id]
        if isinstance(value, Exception):
            raise value
        return value


def inputs():
    case = ResearchCase()
    first = case.known_question()
    second = first.model_copy(update={'reference': first.reference.model_copy(update={'question_id': 'second'})})
    case.task['known_questions'].append(second.reference.model_dump(mode='json'))
    candidate, _ = case.bindings()
    return candidate, first, second


def test_exact_selected_records_are_retained_without_latest_revision_lookup():
    candidate, first, second = inputs()
    peer = Peer({'known': first, 'second': second})
    context = QuestionReader(peer).review(candidate.task)
    assert context.documents() == (first, second) and not context.gaps
    assert peer.calls == [('/v1/questions/read', first.reference), ('/v1/questions/read', second.reference)]


def test_missing_record_is_explicit_and_does_not_hide_other_available_questions():
    candidate, first, second = inputs()
    peer = Peer({'known': ValueError('research_reference_unavailable'), 'second': second})
    context = QuestionReader(peer).review(candidate.task)
    assert context.documents() == (second,)
    assert context.unavailable() == ((first.reference, 'research_reference_unavailable'),)
    result = ResearchProposalValidator().validate(candidate, context).document()
    assert result.questions and result.outcome == 'proposed'
    assert result.findings[0].code == 'research_reference_unavailable'
    assert result.findings[0].location == '/known_questions/0'


@pytest.mark.parametrize('reason', ['research_access_denied', 'research_peer_unavailable', 'research_read_expired',
                                   'research_read_byte_limit', 'research_read_call_limit'])
def test_denial_outage_or_budget_exhaustion_stops_calls_without_fabricating_absence(reason):
    candidate, first, second = inputs()
    peer = Peer({'known': ValueError(reason), 'second': second})
    context = QuestionReader(peer).review(candidate.task)
    assert not context.documents() and len(peer.calls) == 1
    assert context.unavailable() == ((first.reference, reason), (second.reference, reason))


def test_wrong_record_identity_and_invalid_criteria_are_not_accepted_as_context():
    candidate, first, second = inputs()
    peer = Peer({'known': second, 'second': second.model_copy(update={'criteria': second.criteria * 2})})
    context = QuestionReader(peer).review(candidate.task)
    assert not context.documents()
    assert [reason for _, reason in context.unavailable()] == ['research_question_binding', 'research_question_invalid']


def test_programming_error_is_not_downgraded_to_a_missing_question():
    candidate, _, second = inputs()
    with pytest.raises(ValueError, match='unexpected_internal_error'):
        QuestionReader(Peer({'known': ValueError('unexpected_internal_error'), 'second': second})).review(candidate.task)


def test_empty_selection_makes_no_peer_call():
    candidate, _ = ResearchCase().bindings()
    peer = Peer({})
    context = QuestionReader(peer).review(candidate.task)
    assert context.records == context.gaps == () and not peer.calls
