"""Test-only checkpoint process barrier; no production adapter configuration."""

import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.supervision_execution import BudgetTemplates
from amphora_agent_planning.supervision_execution.budget_template import (
    ReviewedBudgetTemplate,
)
from amphora_agent_planning.supervision_execution.worker import CheckpointWorker
from amphora_contracts_core import ArtifactRef, Scope
from sqlalchemy import create_engine


def main():
    phase, location = sys.argv[1:]
    path = Path(location)
    config = json.loads(path.read_bytes())
    principal = Principal(config['actor'], Scope.model_validate(config['scope']),
                          frozenset({'record_requests', 'record_attempts', 'read_attempts'}))

    class Data:
        def artifact(self, ref, budget):
            assert phase == 'crash', 'Recovery must not read Data'
            return ref

        def content(self, ref, budget):
            assert phase == 'crash', 'Recovery must not read Data'
            return bytes.fromhex(config['bodies'][ref.artifact_id])

    class InterruptedProvider:
        def supports(self, model):
            return True

        def reply(self, binding, packet, *, deadline_unix_ms):
            assert phase == 'crash' and packet
            with path.with_suffix('.issued.json').open('x', encoding='utf-8') as stream:
                json.dump({'pid': os.getpid(), 'ordinal': binding.ordinal,
                           'deadline_unix_ms': deadline_unix_ms}, stream)
            # Issuance and packet are already durable. No observation or cleanup.
            os._exit(73)

    templates = BudgetTemplates([(ArtifactRef.model_validate(item['reference']),
        ReviewedBudgetTemplate(item['canonical'].encode())) for item in config['templates']])
    engine = create_engine(os.environ['AMPHORA_CHECKPOINT_PROBE_SQL'],
                           connect_args={'options': '-c statement_timeout=5000'})
    try:
        worker = CheckpointWorker(engine, Data(), templates if phase == 'crash' else None,
                                  InterruptedProvider() if phase == 'crash' else None, timeout_seconds=2)
        outcome = worker.run(principal, config['engagement'])
        print(json.dumps({'pid': os.getpid(), 'stop_reason': outcome.stop_reason,
                          'statuses': [item.observation.document().status if item.observation else 'pending'
                                       for item in outcome.attempts]}))
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        main()
    except Exception:  # noqa: BLE001 - subprocess must never print secret-bearing SQL diagnostics
        print('Checkpoint process probe failed', file=sys.stderr)
        sys.exit(1)
