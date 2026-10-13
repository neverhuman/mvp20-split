"""Opt-in structural declarations; no chemistry toolkit or producer authority."""
import base64
import hashlib
import json
import struct
from dataclasses import dataclass
from amphora_contracts_chemical_structure import StructureResult
from amphora_contracts_core import SchemaRef
from .profiles import CandidateRegistrationError, schema_reference

@dataclass(frozen=True)
class ChemicalCandidateProfile:
    schema: SchemaRef
    kind: str
    semantic_profile: SchemaRef

    def __post_init__(self):
        if self.kind != "finite_molecule" or self.schema != schema_reference("chemical-structure.result"):
            raise CandidateRegistrationError("candidate_profile_invalid")
        if self.semantic_profile.schema_id != "chemical-structure.finite-smiles-2d":
            raise CandidateRegistrationError("candidate_profile_invalid")

    def decode(self, body, scope):
        def unique(pairs):
            values={}
            for key,value in pairs:
                if key in values: raise CandidateRegistrationError("candidate_duplicate_json_key")
                values[key]=value
            return values
        try:
            if type(body) is not bytes or len(body)>262144:
                raise CandidateRegistrationError("candidate_representation_limit")
            data=json.loads(body.decode("utf-8"),object_pairs_hook=unique)
            record=StructureResult.model_validate_json(json.dumps(data,allow_nan=False))
            if record.scope != scope or record.semantic_profile != self.semantic_profile:
                raise CandidateRegistrationError("candidate_representation_binding_mismatch")
            if record.outcome.status != "derived":
                raise CandidateRegistrationError("candidate_structure_not_derived")
            self.validate_bundle(record.outcome)
            return record
        except CandidateRegistrationError:
            raise
        except (ValueError,TypeError,RecursionError,struct.error) as error:
            raise CandidateRegistrationError("candidate_representation_invalid") from error

    @staticmethod
    def validate_bundle(bundle):
        graph=bundle.graph
        indexes=[a.index for a in graph.atoms]
        if indexes != list(range(len(indexes))) or sum(a.atomic_number>1 for a in graph.atoms)>128:
            raise CandidateRegistrationError("candidate_structure_invalid")
        edges=set(); connected={0}
        for bond in graph.bonds:
            edge=tuple(sorted((bond.begin,bond.end)))
            if bond.begin==bond.end or bond.begin not in indexes or bond.end not in indexes or edge in edges:
                raise CandidateRegistrationError("candidate_structure_invalid")
            if any(i not in indexes for i in bond.stereo_atoms):
                raise CandidateRegistrationError("candidate_structure_invalid")
            edges.add(edge)
        for _ in indexes:
            for a,b in edges:
                if a in connected or b in connected: connected.update((a,b))
        if len(connected)!=len(indexes) or sum(a.formal_charge for a in graph.atoms)!=bundle.formula.net_formal_charge:
            raise CandidateRegistrationError("candidate_structure_invalid")
        depiction=bundle.depiction
        png=base64.b64decode(depiction.png_base64,validate=True)
        if len(png)>131072 or hashlib.sha256(png).hexdigest()!=depiction.sha256:
            raise CandidateRegistrationError("candidate_depiction_invalid")
        if len(png)<33 or png[:8]!=b"\x89PNG\r\n\x1a\n" or png[12:16]!=b"IHDR" or struct.unpack(">II",png[16:24])!=(depiction.width,depiction.height):
            raise CandidateRegistrationError("candidate_depiction_invalid")
