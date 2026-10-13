"""Exact profile/environment identity and safe domain failure vocabulary."""
import hashlib
import json
import sys
from dataclasses import dataclass
from importlib.metadata import version
from importlib.resources import files
from amphora_contracts_core import SchemaRef

class StructureProblem(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)

@dataclass(frozen=True)
class DerivationProfile:
    reference: SchemaRef
    environment_sha256: str

    @classmethod
    def load(cls):
        raw=files(__package__).joinpath("profile.json").read_bytes()
        env=files(__package__).joinpath("environment.json").read_bytes()
        pins=json.loads(env)
        if f"{sys.version_info.major}.{sys.version_info.minor}" != pins["python_minor"]:
            raise StructureProblem("error", "derivation_failed")
        if any(version(name)!=expected for name,expected in pins["packages"].items()):
            raise StructureProblem("error", "derivation_failed")
        return cls(SchemaRef(schema_id="chemical-structure.finite-smiles-2d", version="1", sha256=hashlib.sha256(raw).hexdigest()),hashlib.sha256(env).hexdigest())

    def check(self, request):
        if request.semantic_profile != self.reference:
            raise StructureProblem("unsupported", "profile_mismatch")
