import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.knowledge_access.prompt import GraphPrompt

from ..proposals.support import Case

CASES = json.loads((Path(__file__).parent / 'fixtures/predecessor.json').read_text())['cases']


@pytest.mark.parametrize('expected', CASES, ids=['genesis', 'historical', 'legacy'])
def test_extraction_record_and_prompt_bytes_match_predecessor(expected):
    bound = Case(history=expected['history']).bind(legacy=expected['legacy'])
    assert bound.task.sha256 == expected['task_sha256']
    assert hashlib.sha256(bound.knowledge.profile_bytes).hexdigest() == expected['profile_sha256']
    snapshot = bound.knowledge.snapshot_bytes
    assert (None if snapshot is None else hashlib.sha256(snapshot).hexdigest()) == expected['snapshot_sha256']
    assert hashlib.sha256(GraphPrompt.render(bound.review, bound.knowledge)).hexdigest() == expected['prompt_sha256']
