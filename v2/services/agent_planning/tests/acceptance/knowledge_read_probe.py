"""Fresh installed Planning process: public Knowledge reads only, no peer state."""

import hashlib
import importlib.util
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.knowledge_access import KnowledgeReader, KnowledgeReadWindow, KnowledgeTransport
from amphora_contracts_core import Scope


def run(path):
    assert version('amphora-agent-planning') == '0.20.0'
    assert all(importlib.util.find_spec(name) is None for name in
               ('amphora_knowledge', 'amphora_research', 'amphora_data_artifacts', 'amphora_campaign_runtime'))
    document = json.loads(path.read_bytes())
    request = document['request']
    request = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=request['actor_id'],
        scope=Scope.model_validate_json(json.dumps(request['reference']['scope'])))
    task = ExtractionSnapshot.from_bytes(json.dumps(document['task']).encode(), request)
    window = KnowledgeReadWindow()
    reader = KnowledgeReader(KnowledgeTransport(os.environ['PLANNING_KNOWLEDGE_ENDPOINT'], os.environ['PLANNING_KNOWLEDGE_TOKEN']))
    try:
        context = reader.review(task, window)
        return {'pid': os.getpid(), 'status': 'read', 'task_sha256': task.sha256,
                'snapshot': None if context.snapshot_bytes is None else context.snapshot().reference.model_dump(mode='json'),
                'profile_sha256': hashlib.sha256(context.profile_bytes).hexdigest(),
                'snapshot_sha256': None if context.snapshot_bytes is None else hashlib.sha256(context.snapshot_bytes).hexdigest(),
                'calls': window.calls, 'bytes': window.consumed}
    except ValueError as error:
        code = str(error)
        assert code in {'knowledge_access_denied', 'knowledge_reference_unavailable'}
        return {'pid': os.getpid(), 'status': code, 'task_sha256': task.sha256, 'calls': window.calls}


if __name__ == '__main__':
    print(json.dumps(run(Path(sys.argv[1]))))
