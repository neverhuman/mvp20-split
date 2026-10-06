"""Explicit test subprocess: abrupt death after the real durable issuance grant."""

import argparse
import json
import os
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.evaluation_execution import EvaluationRunner
from amphora_agent_planning.providers import FixtureProvider
from amphora_contracts_core import Scope
from sqlalchemy import create_engine


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('mode', choices=['crash', 'recover', 'complete'])
    args = parser.parse_args()
    config = json.loads((args.root / 'configuration.json').read_text())
    actor = Principal(config['actor_id'], Scope.model_validate(config['scope']),
                      frozenset({'record_requests', 'record_attempts', 'read_attempts'}))
    class Provider:
        def supports(self, model):
            return FixtureProvider('abstain').supports(model)
        def reply(self, attempt):
            with (args.root / 'calls.txt').open('a', encoding='utf-8') as stream:
                stream.write(attempt.request.sha256 + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            if args.mode == 'crash':
                os._exit(73)
            return FixtureProvider('abstain').reply(attempt)
    engine = create_engine(os.environ['EVALUATION_PROCESS_SQL'])
    try:
        runner = EvaluationRunner(engine, Provider(), adapter_revision='fixture-1', timeout_seconds=1)
        result = runner.step(actor, config['suite_id'])
        (args.root / (args.mode + '.json')).write_text(json.dumps({'status': result.status, 'passed': result.passed,
            'observations': [item.observation.model_dump(mode='json') for item in result.observations]}), encoding='utf-8')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
