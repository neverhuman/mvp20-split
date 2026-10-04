"""Fresh installed Planning process consuming public Research question records."""

import hashlib
import importlib.util
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.research_access import QuestionReader, ResearchReadWindow, ResearchTransport
from amphora_contracts_core import Scope


def run(path):
    assert version('amphora-agent-planning') == '0.20.0'
    assert all(importlib.util.find_spec(name) is None for name in
               ('amphora_knowledge', 'amphora_research', 'amphora_data_artifacts', 'amphora_campaign_runtime'))
    value = json.loads(path.read_bytes())
    raw = value['request']
    request = RequestSnapshot.from_bytes(json.dumps(raw).encode(), actor_id=raw['actor_id'],
        scope=Scope.model_validate_json(json.dumps(raw['reference']['scope'])))
    task = ExtractionSnapshot.from_bytes(json.dumps(value['task']).encode(), request)
    window = ResearchReadWindow()
    context = QuestionReader(ResearchTransport(os.environ['PLANNING_RESEARCH_ENDPOINT'],
        os.environ['PLANNING_RESEARCH_TOKEN'])).review(task, window)
    return {'pid': os.getpid(), 'task_sha256': task.sha256, 'calls': window.calls,
        'records': [record.model_dump(mode='json') for record in context.documents()],
        'record_sha256': [hashlib.sha256(raw).hexdigest() for raw in context.records],
        'gaps': [{'reference': ref.model_dump(mode='json'), 'reason': reason} for ref, reason in context.unavailable()]}


if __name__ == '__main__':
    print(json.dumps(run(Path(sys.argv[1]))))
