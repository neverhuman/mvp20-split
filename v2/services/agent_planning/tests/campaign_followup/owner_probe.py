"""Test-only installed Planning worker with deterministic targeted future intent."""

import json
import sys
from pathlib import Path

from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.supervision_scheduling.configuration import CheckpointHost
from amphora_contracts_planning import CheckpointFollowupDraft


class TargetedFixture:
    def __init__(self, definition):
        self.definition = definition

    def supports(self, model):
        return (model.provider_id, model.model_id, model.model_revision) == ('deterministic', 'adversarial-fixture', '1')

    def reply(self, binding, packet, *, deadline_unix_ms):
        assert len(packet) <= 8388608
        rows = json.loads(packet)['untrusted_context']['slices']
        selections = [row['payload']['selection'] for row in rows if row['lane'] == 'research']
        assert len(selections) == 1
        selection = selections[0]
        points = selection['criteria']
        assert points and self.definition['scope'] == points[0]['question']['scope']
        intent = {'question': points[0]['question'], 'needs': [points[0]['need']], 'assessments': [],
            'producer': None, 'expected_evidence': 'A second synthetic result beside the retained first result.',
            'uncertainty': 'This software fixture establishes no scientific improvement.'}
        value = {'schema_version': '3', 'authority': 'proposal_only', 'scientific_authority': 'not_established',
            'action': 'propose_campaign', 'rationale': 'Synthetic follow-up: vary one value and retain the original for comparison.',
            'decision_scope': binding.request.document().decision_scope, 'focus_artifact': selection['focus_artifact'],
            'candidate': {'kind': 'future_campaign', 'title': 'Targeted synthetic follow-up', 'definition': self.definition, 'expected_evidence': [intent]},
            'alternatives': [], 'evidence_requests': [],
            'targets': [{'criterion': points[0], 'improvement': 'Produce a second bounded observation for comparison.',
                         'expected_learning': 'Whether the selected synthetic input changes the recorded result.'}],
            'unresolved': [{'criterion': point, 'posture': 'unknown', 'description': 'Requires later evidence; not resolved by campaign completion.'} for point in points]}
        return ProviderReply((CheckpointFollowupDraft.model_validate_json(json.dumps(value)).model_dump_json().encode(),), unknown_usage())


def main(config, candidate):
    raw = candidate.read_bytes()
    assert len(raw) <= 262144
    host = CheckpointHost.load(config)
    try:
        host.poller.worker.provider = TargetedFixture(json.loads(raw))
        print(json.dumps(host.poller.sweep(host.principal, seconds=0.5, interval=0.05)))
    finally:
        host.close()


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
