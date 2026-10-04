"""Research-local synthetic question setup; not a public registration proof."""

import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_contracts_research import ResearchQuestion
from amphora_research.persistence.ledger import IdentityLedger
from sqlalchemy import create_engine


def run(stage, path):
    assert version('amphora-research') == '0.33.0'
    question = ResearchQuestion.model_validate_json(path.read_bytes())
    if stage == 'advance':
        question = question.model_copy(update={'reference': question.reference.model_copy(update={'revision': 2}),
            'supersedes': question.reference, 'objective': 'Revised synthetic question for a future campaign'})
    engine = create_engine(os.environ['PLANNING_RESEARCH_DATABASE'], connect_args={'options': '-c statement_timeout=5000'})
    try:
        stored = IdentityLedger(engine).publish(question.reference.scope, question)
        return {'pid': os.getpid(), 'question': stored.model_dump(mode='json'),
                'authority': 'synthetic_owner_local_read_fixture_only'}
    finally:
        engine.dispose()


if __name__ == '__main__':
    try:
        print(json.dumps(run(sys.argv[1], Path(sys.argv[2]))))
    except Exception as error:
        raise SystemExit('Research read fixture failed: ' + type(error).__name__) from None
