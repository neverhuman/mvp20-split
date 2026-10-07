"""Incremental owner reads must complete before full criterion membership checks."""

import pytest
from amphora_agent_planning.campaign_context import ResearchSelection
from amphora_agent_planning.campaign_followup.policy import canonical
from amphora_agent_planning.campaign_research_access import ResearchRecordReader

from ..campaign_research_access.test_reader import Peer, PATHS
from .test_binding import setup


def selected_peer():
    request, value, records = setup()
    peer = Peer()
    peer.values = {PATHS[kind]: records[field][0] for kind, field in
        [('question', 'questions'), ('need', 'needs'), ('assessment', 'assessments')]}
    return ResearchSelection.from_bytes(canonical(value), request), peer


def test_followup_reader_preserves_full_selection_after_all_three_public_reads():
    selection, peer = selected_peer()
    report = ResearchRecordReader(peer).review(selection)
    assert report.calls == 3 and not report.failures
    assert report.context.selection == selection
    assert len(report.context.selection.document().criteria) == 1


def test_unavailable_selected_identity_does_not_get_published_as_bound_intent():
    selection, peer = selected_peer()
    peer.values[PATHS['need']] = ValueError('research_access_denied')
    with pytest.raises(ValueError, match='followup_criterion_record_unavailable'):
        ResearchRecordReader(peer).review(selection)
    assert len(peer.calls) == 3
