import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_polymer_space import PROFILE, EQUIVALENCE
from amphora_polymer_space.adapter import SpaceWorkerAdapter
from amphora_polymer_space.capability import SpaceCapability
from amphora_polymer_space.canonicalization import canonicalize
from amphora_tool_protocol import ToolInputRejected

ROOT=Path(__file__).absolute().parents[4]


def design():
    data=json.loads((Path(__file__).parent.parent/'legality/request.json').read_bytes())['source']
    data['profile']=PROFILE.model_dump(mode='json')
    return data


def execute(data):
    adapter=SpaceWorkerAdapter('canonicalize')
    adapter.descriptor('c'*64)
    raw=json.dumps(data).encode()
    return CanonicalCandidate.model_validate_json(adapter.execute(raw)),raw


def test_receipt_binds_exact_bytes_scope_and_versioned_semantics():
    result,raw=execute(design())
    assert result.authority=='synthetic_encoding' and result.kind=='polymer'
    assert result.source_sha256==hashlib.sha256(raw).hexdigest()
    assert result.semantic_profile==PROFILE and result.equivalence_profile==EQUIVALENCE
    assert result.scope.model_dump(mode='json')==design()['scope']
    differently_encoded=json.dumps(design(),indent=2,sort_keys=True).encode()
    other=CanonicalCandidate.model_validate_json(canonicalize(differently_encoded))
    assert result.canonical_sha256==other.canonical_sha256
    assert result.source_sha256!=other.source_sha256


def test_canonical_capability_has_distinct_input_output_pins_and_safe_default_move():
    capability=SpaceCapability('canonicalize')
    assert capability.descriptor('c'*64).tool.binding.capability_id=='synthetic.polymer-canonicalize'
    assert SpaceCapability().descriptor('c'*64).tool.binding.capability_id=='synthetic.polymer-move'
    for direction in ('input','output'):
        reference=capability.schema_ref(direction)
        assert capability.schema_bytes(direction)==(ROOT/'contracts/schemas/v1'/(reference.schema_id+'.validation.json')).read_bytes()
    for direction in ('schema_bytes','schema_ref'):
        with pytest.raises(ValueError):getattr(capability,direction)('bad')
    with pytest.raises(ValueError):SpaceCapability('repair')


@pytest.mark.parametrize('raw',[b'{"kind":"polymer","kind":"polymer"}',b'{"x":NaN}',b'['*1100,b'{}',b'\xff',b'x'*262145,'text'],ids=['duplicate','nonfinite','depth','missing','encoding','capacity','type'])
def test_malformed_duplicate_nonfinite_and_unbounded_source_is_rejected_safely(raw):
    adapter=SpaceWorkerAdapter('canonicalize');adapter.descriptor('c'*64)
    with pytest.raises(ToolInputRejected) as error:adapter.execute(raw)
    assert error.value.reason_code=='invalid_polymer_space_canonicalize'


def test_direct_function_enforces_byte_bound():
    with pytest.raises(ValueError):canonicalize('text')
    with pytest.raises(ValueError):canonicalize(b'x'*262145)


def test_canonicalization_cli_uses_same_public_worker_contract():
    def cli(*args,body=None):
        return subprocess.run([sys.executable,'-m','amphora_polymer_space',*args],input=body,capture_output=True,timeout=30)
    descriptor=cli('describe','--operation','canonicalize','--image-sha256','c'*64)
    assert descriptor.returncode==0
    assert json.loads(descriptor.stdout)['tool']['binding']['capability_id']=='synthetic.polymer-canonicalize'
    result=cli('compute','--operation','canonicalize','--image-sha256','c'*64,body=json.dumps(design()).encode())
    assert result.returncode==0 and CanonicalCandidate.model_validate_json(result.stdout).kind=='polymer'
    schema=cli('schema','--operation','canonicalize','--direction','output')
    assert schema.returncode==0 and schema.stdout==SpaceCapability('canonicalize').schema_bytes('output')
