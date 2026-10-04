"""Installed Knowledge host and synthetic task preparation for read acceptance."""

import hashlib
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from importlib.resources import files
from pathlib import Path

from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot
from amphora_agent_planning.proposals.context import proposal_schema
from amphora_contracts_core import Scope
from amphora_contracts_planning import extraction_edit_schema

ROOT = Path(__file__).absolute().parents[1]


def rescope(value, scope):
    if isinstance(value, dict):
        if set(value) == {'tenant_id', 'project_id'}:
            value.update(scope)
        for item in value.values():
            rescope(item, scope)
    elif isinstance(value, list):
        for item in value:
            rescope(item, scope)


def task_file(path, prepared, *, genesis=False, scope=None, unavailable=False):
    value = json.loads((ROOT / 'services/agent_planning/tests/extraction/fixtures/extraction.json').read_bytes())
    graph = prepared['profile']['graph']
    rescope(value, graph['scope'])
    request, task = value['request'], value['task']
    prompt = files('amphora_agent_planning.extraction').joinpath('prompts/domain-decomposition-v2.txt').read_bytes()
    request['context']['prompt'].update(sha256=hashlib.sha256(prompt).hexdigest(), size_bytes=len(prompt))
    request['context']['output_schema'] = extraction_edit_schema().model_dump(mode='json')
    task.update(schema_version='2', existing_entities=[row['reference'] for row in prepared['snapshot']['content']['entities']],
                existing_assertions=[row['reference'] for row in prepared['snapshot']['content']['assertions']])
    task['target'].update(graph=graph, base=prepared['head'], vocabulary=prepared['profile']['vocabulary_reference'],
                          policy=prepared['profile']['policy'], operation_schema=proposal_schema().model_dump(mode='json'))
    if genesis:
        task['target'].update(graph=dict(graph, graph_id='unreserved-genesis'), base=None)
        task.update(existing_entities=[], existing_assertions=[])
    if unavailable:
        task['target']['base']['snapshot']['sha256'] = 'f' * 64
    if scope is not None:
        rescope(value, scope)
    bound = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=request['actor_id'],
                                      scope=Scope.model_validate_json(json.dumps(request['reference']['scope'])))
    task['request_sha256'] = bound.sha256
    ExtractionSnapshot.from_bytes(json.dumps(task).encode(), bound)
    path.write_text(json.dumps({'request': request, 'task': task}), encoding='utf-8')
    return path


class ReadOwnerHost:
    def __init__(self, python, config, environment, *, module='amphora_knowledge'):
        assert module in {'amphora_knowledge', 'amphora_research'}
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        self.endpoint = f'http://127.0.0.1:{port}'
        self.process = subprocess.Popen([str(python), '-I', '-m', module, 'serve', '--config',
            str(config), '--port', str(port)], env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                assert self.process.poll() is None, 'Read owner host exited before readiness'
                try:
                    with urllib.request.urlopen(self.endpoint + '/health', timeout=1) as response:
                        assert response.status == 200
                        return
                except (urllib.error.URLError, TimeoutError):
                    time.sleep(0.05)
            raise RuntimeError('Read owner host readiness deadline')
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=10)


# Compatibility for the retained Knowledge-only fixture harness.
KnowledgeHost = ReadOwnerHost
