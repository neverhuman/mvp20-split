"""Run only in the independently installed Planning interpreter; synthetic provider."""
import base64
import copy
import cProfile
import importlib.util
import json
import pstats
import sys
import time
from dataclasses import asdict
from pathlib import Path

from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions
from amphora_agent_planning.curation_budget import CurationAllowance
from amphora_agent_planning.curation_input import curation_tokenizer_reference
from amphora_agent_planning.curation_worker.hosting import CurationHost
from amphora_agent_planning.providers.port import ProviderReply
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_contracts_planning import ProviderUsage


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


class SyntheticProposal:
    """The sole replaced component. Public peers and durable workflow remain real."""
    def __init__(self, output):
        self.output = output

    def supports(self, _model):
        return True

    def validate_policy(self, policy):
        CurationAllowance.validate_policy(policy)

    def reply(self, binding, packet, *, deadline_unix_ms):
        assert deadline_unix_ms > int(time.time() * 1000)
        path = self.output / 'synthetic-provider-issued.json'
        # Exclusive issuance marker detects unexpected physical re-entry.
        with path.open('x', encoding='utf-8') as stream:
            json.dump({'ordinal': binding.ordinal, 'external_calls': 0, 'kind': 'deterministic_test_adapter'}, stream)
        record = json.loads(packet)['untrusted_context']
        runtime = next(row['payload'] for row in record['slices'] if row['lane'] == 'curation_runtime')
        declarations = []
        for row in record['slices']:
            encoded = row['payload'].get('body_base64') if isinstance(row['payload'], dict) else None
            if encoded:
                try:
                    body = json.loads(base64.b64decode(encoded))
                except (ValueError, UnicodeError):
                    continue
                if isinstance(body, dict) and body.get('format') == 'planning-campaign-decision.v2':
                    declarations.append(body)
        assert len(declarations) == 1
        future = declarations[0]['future']
        graph = copy.deepcopy(runtime['draft']['definition'])
        graph['revision'], graph['context'] = future['revision'], future['context']
        value_type = graph['body']['outputs'][0]['value_type']
        graph['body']['inputs'].append({'name': 'previous_result', 'value_type': value_type})
        graph['body']['outputs'].append({'name': 'previous_result', 'value_type': value_type})
        finish = next(node for node in graph['body']['nodes'] if node['kind'] == 'finish')
        finish['outputs'].append({'port': 'previous_result', 'source': {'kind': 'input', 'name': 'previous_result'}})
        response = {'schema_version': '1', 'profile': 'planning.campaign-curation-draft.v1',
            'authority': 'proposal_only', 'scientific_authority': 'not_established',
            'decision_scope': record['request']['decision_scope'],
            'rationale': 'Deterministic integration fixture: retain the exact predecessor result and run a fresh synthetic seed. No live model reasoning or scientific improvement is claimed.',
            'outcome': {'kind': 'propose_campaign', 'candidate': {'kind': 'future_campaign',
                'title': 'Synthetic successor with retained predecessor', 'definition': graph, 'expected_evidence': []}, 'gaps': []},
            'unresolved': []}
        raw = json.dumps(response).encode()
        (self.output / 'synthetic-provider-response.json').write_bytes(raw)
        return ProviderReply([raw], ProviderUsage(input_tokens=0, output_tokens=0, accounting_units=0, certainty='reported'))


def main():
    assert all(importlib.util.find_spec(name) is None for name in (
        'amphora_campaign_runtime', 'amphora_data_artifacts', 'amphora_research',
        'amphora_knowledge', 'amphora_capability_registry', 'amphora_deployment'))
    action, path = sys.argv[1], Path(sys.argv[2])
    if action == 'material':
        write(path, {'instructions': reviewed_instructions('curation').decode(),
            'tokenizer': curation_tokenizer_reference().model_dump(mode='json'),
            'output_schema': campaign_curation_draft_schema().model_dump(mode='json')})
        return
    assert action in {'run', 'profile'}
    host = CurationHost.load(path)
    try:
        if action == 'profile':
            # Planning owns these reads. No lease, peer write or provider call.
            journal = host.poller.worker.compiler.progression.journal
            rows = (path.parent / 'compiler-turns.jsonl').read_text().splitlines()
            selection_id = json.loads(rows[-1])['selection_id']
            timings = []
            profiler = cProfile.Profile()
            profiler.enable()
            for repetition in range(2):
                started = time.perf_counter()
                selected = journal.selected(host.principal, selection_id)
                context = journal.context(host.principal, selected.selection)
                save, _ = context.save()
                journal.read(host.principal, selection_id, save.effect_id)
                current = journal.latest_round(host.principal, selection_id)
                timings.append({'repetition': repetition, 'seconds': time.perf_counter() - started,
                    'round': None if current is None else current.ordinal})
            profiler.disable()
            profiler.dump_stats(str(path.parent / 'compiler-read-profile.pstats'))
            with (path.parent / 'compiler-read-profile.txt').open('w') as stream:
                pstats.Stats(profiler, stream=stream).sort_stats('cumulative').print_stats(45)
            write(path.parent / 'compiler-read-timings.json', timings)
            return
        host.poller.worker.executor.provider = SyntheticProposal(path.parent)
        progression = host.poller.worker.compiler.progression
        advance = progression.advance
        consecutive_checks = 0
        def traced_advance(*args, **kwargs):
            nonlocal consecutive_checks
            started = time.perf_counter()
            result = advance(*args, **kwargs)
            dispatch = result.dispatch
            detail = {'selection_id': result.selection_id, 'stage': result.stage,
                'terminal': result.terminal, 'pause_reason': result.pause_reason,
                'operation': None if dispatch is None else dispatch.operation.progress.state,
                'prerequisites': None if dispatch is None or dispatch.prerequisites is None else dispatch.prerequisites.status,
                'round': None if result.round is None else result.round.ordinal,
                'elapsed_seconds': time.perf_counter() - started}
            with (path.parent / 'compiler-turns.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(detail) + '\n')
            consecutive_checks = consecutive_checks + 1 if result.stage == 'eligibility' else 0
            assert consecutive_checks < 2, 'Repeated eligibility without validation: diagnose before consuming more rounds'
            return result
        progression.advance = traced_advance
        turns = []
        for _ in range(20):
            turn = host.poller.tick(host.principal)
            turns.append(None if turn is None else asdict(turn))
            write(path.parent / 'worker-turns.json', turns)
            if turn is not None and turn.status == 'terminal':
                assert turn.phase == 'ready', turns
                return
            time.sleep(.2)
        raise AssertionError('Curation did not reach ready within bounded turns')
    finally:
        host.close()


if __name__ == '__main__':
    main()
