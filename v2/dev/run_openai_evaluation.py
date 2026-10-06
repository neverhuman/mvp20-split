"""Execute/resume the one frozen initial suite; every call uses durable Planning issuance."""
import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from amphora_agent_planning.evaluation_batch.storage import EvaluationJournal
from amphora_agent_planning.evaluation_execution import EvaluationRunner
from amphora_agent_planning.openai_provider.http import OpenAIHTTP
from sqlalchemy import URL, create_engine

from openai_evaluation_bundle import load_bundle
from postgres_fixture import owned_state


def credential(path):
    key = os.environ.get('OPENAI_API_KEY')
    if key:
        return key
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        name, separator, value = line.partition('=')
        if separator and name.strip() == 'OPENAI_API_KEY':
            key = value.strip().strip('"').strip("'")
            if key:
                return key
    raise ValueError('openai_credentials_missing')


def report(runner, principal, protocol, batch):
    run = runner.read(principal, protocol.manifest.suite_id)
    rows = []
    for task in batch.tasks:
        attempt = runner.runner.journal.read_attempt(principal, task.binding.reference())
        settlement = runner.runner.settlements.read(principal, task.binding.reference())
        observation = attempt.observation if attempt else None
        wire = observation.document() if observation else None
        rows.append({'case': task.case_id, 'repetition': task.repetition,
                     'request_sha256': task.request.sha256,
                     'status': wire.status if wire else 'not_observed',
                     'reason_code': wire.reason_code if wire else None,
                     'usage': wire.usage.model_dump(mode='json') if wire else None,
                     'charge': asdict(settlement.charge) if settlement else None,
                     'output_sha256': wire.output_sha256 if wire else None,
                     'output': observation.capture.content.decode('utf-8', errors='replace') if observation else None})
    reported = sum(row['usage']['accounting_units'] or 0 for row in rows if row['usage'])
    return {'timestamp_local': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'suite_id': protocol.manifest.suite_id, 'protocol_sha256': protocol.sha256,
            'batch_sha256': batch.sha256, 'status': run.status, 'passed': run.passed,
            'initial_ceiling_usd_nanodollars': 1000000000, 'reserved_usd_nanodollars': batch.accounting_units,
            'reported_estimated_usd_nanodollars': reported,
            'unknown_usage': sum(row['usage'] is not None and row['usage']['certainty'] != 'reported' for row in rows),
            'score': asdict(run.score), 'attempts': rows,
            'limits': ['Synthetic engineering corpus only; no scientific efficacy or target-host claim',
                       'Reported estimated token cost is not an invoice; unknown calls retain reservation']}


def execute(output, key_file, *, read_only=False):
    output.mkdir(parents=True, exist_ok=False)
    # Read-only report needs no secret and cannot send requests.
    transport = None if read_only else OpenAIHTTP(credential(key_file))
    principal, protocol, batch, provider = load_bundle(transport)
    state = owned_state()
    host, port = state['endpoint'].split(':')
    url = URL.create('postgresql+psycopg', username='planning_service', password=state['password'],
                     host=host, port=int(port), database=state['database'])
    engine = create_engine(url, connect_args={'options': '-c statement_timeout=5000'})
    try:
        runner = EvaluationRunner(engine, provider, adapter_revision=provider.revision, timeout_seconds=60)
        if not read_only:
            EvaluationJournal(engine).register(principal, protocol, batch)
        current = report(runner, principal, protocol, batch)
        for index in range(len(batch.tasks)):
            (output / f'checkpoint-{index:02d}.json').write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
            if read_only or current['status'] != 'pending' or current['unknown_usage']:
                break
            if any(row['status'] in {'unknown', 'unavailable'} for row in current['attempts']):
                break
            before = sum(row['status'] != 'not_observed' for row in current['attempts'])
            runner.step(principal, protocol.manifest.suite_id)
            current = report(runner, principal, protocol, batch)
            after = sum(row['status'] != 'not_observed' for row in current['attempts'])
            print(json.dumps({'completed': after, 'planned': len(batch.tasks),
                              'reported_estimated_usd': current['reported_estimated_usd_nanodollars'] / 1000000000,
                              'status': current['status']}), flush=True)
            if after == before:
                break  # Another issued worker or unknown outcome; never busy retry.
        (output / 'evidence.json').write_text(json.dumps(current, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'passed': current['passed'], 'status': current['status'],
                          'evidence': str(output / 'evidence.json')}), flush=True)
    finally:
        engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--key-file', type=Path, default=Path('Z:/ssos/.env'))
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    execute(args.output.absolute(), args.key_file, read_only=not args.execute)
