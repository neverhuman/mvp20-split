"""Actual SQL response replay preserves explicit scalar proposal bytes without applying them."""

import json
from dataclasses import replace

from amphora_campaign_runtime.supervision_journal.checkpoint_frames import (
    CheckpointFrame,
)
from amphora_campaign_runtime.supervision_journal.responses import ResponseJournal
from amphora_contracts_supervision import parse_supervision_command

from ..supervision_responses.test_checkpoint_output import exchange
from .test_checkpoint_storage import command, setup


def test_new_scalar_profile_response_survives_journal_reconstruction(graph_env):
    journal, original = setup(graph_env)
    bound, footprint, record, raw = exchange(original=original)
    frame = CheckpointFrame.capture(bound.document(), footprint,
        prepared_by=graph_env.env.principal.actor_id, planning_actor='fixture')
    journal.prepare(graph_env.env.principal, frame, command(frame).canonical_bytes)
    actor = replace(graph_env.env.principal, actor_id='fixture', actions=frozenset({'read', 'supervise_respond'}))
    incoming = parse_supervision_command('runtime.supervision.respond', json.dumps({
        'encoding': 'amphora-command-v2', 'identity': {'scope': actor.scope.model_dump(mode='json'),
            'actor_id': 'fixture', 'command_family': 'runtime.supervision.respond', 'command_id': 'exact-scalar-response'},
        'payload': record.model_dump(mode='json')}))
    responses = ResponseJournal(journal)
    first = responses.record(actor, incoming, capture_bytes=raw)
    saved = responses.response(actor, record.response_id)
    assert first.outcome.status == 'recorded' and saved.capture_bytes == raw
    replacement = ResponseJournal(journal)
    assert replacement.record(actor, incoming, capture_bytes=raw) == first
    assert replacement.response(actor, record.response_id) == saved
    assert b'0.1234567890123456789' in saved.capture_bytes
