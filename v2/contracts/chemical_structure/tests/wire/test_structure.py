import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from amphora_contracts_chemical_structure import StructureRequest, StructureResult

EXAMPLE = Path(__file__).parents[2] / "examples/supplied-request.json"

def request():
    return json.loads(EXAMPLE.read_bytes())

def test_request_roundtrip_preserves_explicit_identity():
    value=StructureRequest.model_validate(request())
    assert StructureRequest.model_validate_json(value.model_dump_json()) == value
    assert value.smiles == "OCCO" and value.candidate.revision == 1

@pytest.mark.parametrize("field,value", [("origin","generated"),("representation_kind","polymer_repeat"),("smiles","C"*4097),("formula","C2H6O2")])
def test_request_rejects_unapproved_or_untrusted_fields(field,value):
    data=request(); data[field]=value
    with pytest.raises(ValidationError): StructureRequest.model_validate(data)

def test_foreign_candidate_scope_rejected():
    data=request(); data["candidate"]["scope"]["project_id"]="other"
    with pytest.raises(ValidationError): StructureRequest.model_validate(data)

@pytest.mark.parametrize("status",["invalid","unsupported","error"])
def test_failure_has_no_success_authority_or_bundle(status):
    data=request(); del data["smiles"]
    data.update(source_sha256="0"*64,outcome={"status":status,"code":"unsupported_feature"})
    assert StructureResult.model_validate(data).outcome.status == status
    data["outcome"]["authority"]="structural_derivation"
    with pytest.raises(ValidationError): StructureResult.model_validate(data)

def test_incomplete_success_rejected():
    data=request(); del data["smiles"]
    data.update(source_sha256="0"*64,outcome={"status":"derived","authority":"structural_derivation"})
    with pytest.raises(ValidationError): StructureResult.model_validate(data)
