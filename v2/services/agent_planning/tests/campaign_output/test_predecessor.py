"""Literal observations emitted by an independently installed predecessor."""

import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.persistence.records import verified_observation
from amphora_agent_planning.providers import observe
from amphora_contracts_core import Scope

from ..providers.test_task_output import Response

VECTORS = json.loads((Path(__file__).parent / 'fixtures/predecessor-extraction.json').read_bytes())


@pytest.mark.parametrize('case', VECTORS['cases'], ids=lambda value: value['name'])
def test_predecessor_extraction_observation_and_capture_are_byte_identical(case):
    request = case['request']
    snapshot = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=request['actor_id'],
                                         scope=Scope.model_validate(request['reference']['scope']))
    binding = AttemptBinding(snapshot, 1)
    observed = observe(binding, Response(case['capture_utf8'].encode()))
    assert observed.canonical == case['observation_json'].encode()
    assert hashlib.sha256(observed.canonical).hexdigest() == case['observation_sha256']
    assert observed.capture.content == case['capture_utf8'].encode()
    assert verified_observation(binding, observed) == observed
