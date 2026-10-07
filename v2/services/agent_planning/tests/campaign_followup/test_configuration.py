"""Configured Research reader and deterministic fixture; no real model or peer calls."""

import json
import time

import pytest
from amphora_agent_planning.context import AttemptBinding
from amphora_agent_planning.supervision_scheduling.configuration import CheckpointHost
from amphora_agent_planning.supervision_scheduling.fixture import CheckpointFixture
from amphora_contracts_core import ArtifactRef
from amphora_contracts_planning import CheckpointFollowupDraft

from ..supervision_scheduling.test_configuration import configuration
from .test_worker import system

pytestmark = pytest.mark.postgres


def test_configured_seed_is_pinned_and_fixture_preserves_unresolved_selection(stored, tmp_path, monkeypatch):
    worker, data, _, _, intake = system(stored)
    path, raw = configuration(stored, tmp_path, monkeypatch)
    seed = json.loads(worker.followup.seeds[0])
    reference = ArtifactRef.model_validate(seed['budget_template'])
    template = worker.templates.require(reference)
    (tmp_path / 'followup-seed.json').write_text(json.dumps(seed), encoding='utf-8')
    (tmp_path / 'followup-template.json').write_bytes(template.canonical)
    raw.update(templates=[{'reference': seed['budget_template'], 'path': 'followup-template.json'}],
        followup={'research': raw['data'], 'seeds': ['followup-seed.json']})
    path.write_text(json.dumps(raw), encoding='utf-8')
    host = CheckpointHost.load(path)
    try:
        assert host.poller.worker.followup.seeds == worker.followup.seeds
        assert host.poller.worker.provider is None
    finally:
        host.close()
    packet = worker._packet(stored.principal, intake)
    reply = CheckpointFixture('fixture_abstain').reply(AttemptBinding(intake.planning, 1),
        packet.preparation.packet.canonical, deadline_unix_ms=int(time.time() * 1000) + 1000)
    result = CheckpointFollowupDraft.model_validate_json(b''.join(reply.chunks))
    assert result.action == 'abstain' and not result.targets and len(result.unresolved) == 1
    seed['budget_template']['sha256'] = 'f' * 64
    (tmp_path / 'followup-seed.json').write_text(json.dumps(seed), encoding='utf-8')
    with pytest.raises(ValueError, match='budget_template_unavailable'):
        CheckpointHost.load(path)
