"""Planning-owned delayed provider for actual peer integration, never live models."""

import base64
import json
import os
import sys
import time
from pathlib import Path

from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.supervision_scheduling.configuration import CheckpointHost
from amphora_contracts_planning import CheckpointDraft
from amphora_contracts_supervision import CheckpointContext


def main():
    config, engagement, mode, folder = sys.argv[1:]
    root = Path(folder)
    host = CheckpointHost.load(config)

    class DelayedFixture:
        def supports(self, model):
            return (model.provider_id, model.model_id, model.model_revision) == ('deterministic', 'adversarial-fixture', '1')

        def reply(self, binding, packet, *, deadline_unix_ms):
            slices = json.loads(packet)['untrusted_context']['slices']
            declaration = next(item for item in slices if item['identity']['sha256'] == binding.request.document().decision_scope)
            context = CheckpointContext.model_validate_json(base64.b64decode(declaration['payload']['body_base64']))
            candidate = {'kind': 'materialization_adjustment', 'cut': context.snapshot.cut.model_dump(mode='json'),
                'checkpoint_seed_sha256': context.checkpoint_seed_sha256, 'changes': [{
                    'target': context.target.model_dump(mode='json'), 'field_name': 'a',
                    'previous_value_sha256': context.fields[0].original_value_sha256,
                    'proposed': {'kind': 'integer', 'value': 2}}], 'expected_evidence': []}
            if mode == 'future':
                definition = json.loads((root / 'graph.json').read_bytes())
                definition['revision'] += 1
                target = next(item for item in definition['body']['nodes'] if item['node_id'] == 'pack')
                target['fields'][0]['source']['value'] = 5
                candidate = {'kind': 'future_campaign', 'title': 'Next synthetic campaign',
                             'definition': definition, 'expected_evidence': []}
            draft = CheckpointDraft.model_validate_json(json.dumps({'schema_version': '2', 'authority': 'proposal_only',
                'scientific_authority': 'not_established', 'action': 'propose_campaign',
                'rationale': 'Synthetic delayed owner proof', 'decision_scope': binding.request.document().decision_scope,
                'candidate': candidate, 'evidence_requests': [], 'alternatives': [], 'unresolved': []}))
            with (root / 'provider-entered.json').open('x', encoding='utf-8') as stream:
                json.dump({'pid': os.getpid(), 'ordinal': binding.ordinal, 'deadline_unix_ms': deadline_unix_ms}, stream)
            end = time.monotonic() + 180
            while not (root / 'provider-release').exists():
                if time.monotonic() >= end:
                    raise TimeoutError('Provider test barrier expired')
                time.sleep(0.05)
            return ProviderReply([draft.model_dump_json().encode()], unknown_usage())

    try:
        host.poller.worker.provider = DelayedFixture()
        host.poller.worker.timeout_seconds = 2 if mode == 'late' else 180
        outcome = host.poller.worker.run(host.principal, engagement)
        (root / 'provider-finished.json').write_text(json.dumps({'pid': os.getpid(), 'stop_reason': outcome.stop_reason,
            'statuses': [attempt.observation.document().status for attempt in outcome.attempts]}), encoding='utf-8')
    finally:
        host.close()


if __name__ == '__main__':
    try:
        main()
    except Exception:  # noqa: BLE001 - do not expose secret-bearing peer or SQL diagnostics
        print('Planning owner probe failed', file=sys.stderr)
        sys.exit(1)
