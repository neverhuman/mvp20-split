"""Bounded byte boundary and explicit domain-to-wire result factory."""
import hashlib
import json
from dataclasses import dataclass
from pydantic import ValidationError
from amphora_contracts_chemical_structure import StructureRequest, StructureResult, StructureFailure
from .profile import DerivationProfile, StructureProblem
from .molecule import ParsedMolecule
from .display import DisplayBundle

@dataclass(frozen=True)
class Derivation:
    request: StructureRequest
    source_sha256: str

    def result(self, outcome):
        identity=self.request.model_dump(exclude={"smiles"})
        return StructureResult.model_validate({**identity,"source_sha256":self.source_sha256,"outcome":outcome})

    def run(self):
        try:
            profile=DerivationProfile.load()
            profile.check(self.request)
            molecule=ParsedMolecule.from_smiles(self.request.smiles)
            outcome=DisplayBundle(molecule,profile).to_wire()
        except StructureProblem as error:
            outcome=StructureFailure(status=error.status,code=error.code)
        except (RuntimeError, ValueError, OverflowError):
            outcome=StructureFailure(status="error",code="derivation_failed")
        return self.result(outcome)

def compute(payload):
    if not isinstance(payload,bytes) or len(payload)>262144:
        raise ValueError("invalid_chemical_request")
    try:
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:
                    raise ValueError("invalid_chemical_request")
                result[key]=value
            return result
        data=json.loads(payload.decode("utf-8"),object_pairs_hook=unique)
        request=StructureRequest.model_validate_json(json.dumps(data,allow_nan=False))
    except (ValidationError, ValueError, RecursionError):
        raise ValueError("invalid_chemical_request") from None
    derivation=Derivation(request,hashlib.sha256(payload).hexdigest())
    result=derivation.run().model_dump_json().encode("utf-8")
    if len(result)>262144:
        result=derivation.result(StructureFailure(status="error",code="size_limit")).model_dump_json().encode("utf-8")
    return result
