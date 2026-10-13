"""Explicit reviewed structural grants shared by activation and selection."""
from dataclasses import dataclass
from importlib.resources import files
import hashlib
import json
from amphora_contracts_core import Scope, SchemaRef
from amphora_contracts_tools import LockEntry
from ..descriptors.identity import ReleaseDocument
from ..descriptors.assessments import Assessment

CONTEXT="supplied-finite-molecules"
PROFILE="supplied-finite-structure-v1"

@dataclass(frozen=True)
class StructuralGrant:
    scope: Scope
    release: LockEntry
    semantic_profile: SchemaRef
    context: str = CONTEXT

    def __post_init__(self):
        pins=json.loads(files(__package__).joinpath("reviewed.json").read_bytes())
        binding=self.release.tool
        if (self.context!=CONTEXT or self.semantic_profile.model_dump()!=pins["semantic_profile"]
            or binding.capability_id!="chemistry.chemical-structure" or binding.release!="0.1.0"
            or binding.contract_version!="1" or self.release.checkpoint_schema is not None):
            raise ValueError("structural_grant_invalid")
        for ports,key,name in ((self.release.input_schemas,"input","structure"),(self.release.output_schemas,"output","result")):
            if len(ports)!=1 or ports[0].port!=name or ports[0].schema_ref.model_dump()!=pins[key]:
                raise ValueError("structural_grant_schema_mismatch")

    def record(self):
        return {"scope":self.scope.model_dump(),"release":self.release.model_dump(mode="json"),"semantic_profile":self.semantic_profile.model_dump(),"context":self.context}

@dataclass(frozen=True)
class StructuralPolicy:
    grants: tuple[StructuralGrant,...] = ()

    def __post_init__(self):
        if type(self.grants) is not tuple or len(self.grants)>64 or any(type(g) is not StructuralGrant for g in self.grants):
            raise ValueError("structural_grants_invalid")
        keys=[(g.scope,g.release.descriptor_sha256) for g in self.grants]
        if len(set(keys))!=len(keys): raise ValueError("structural_grants_ambiguous")

    def matches(self,scope,descriptor,context=CONTEXT):
        if descriptor.authority_ceiling!="evidence_proposal" or descriptor.tool.side_effects!="pure" or descriptor.egress.mode!="deny" or context!=CONTEXT or context not in descriptor.tool.applicability:
            return False
        lock=ReleaseDocument.from_descriptor(descriptor).to_lock()
        return any(g.scope==scope and g.context==context and g.release==lock for g in self.grants)

    def can_activate(self,scope,descriptor):
        legacy=(descriptor.authority_ceiling=="synthetic_only" and descriptor.tool.side_effects=="pure" and "synthetic-tests" in descriptor.tool.applicability)
        return legacy or self.matches(scope,descriptor)

    def assess(self,descriptor,need,report):
        if not report.valid: return Assessment("unreviewed",("descriptor_invalid",))
        if not self.matches(need.scope,descriptor,need.context):
            return Assessment("ineligible",("structural_profile_not_authorized",))
        return Assessment("eligible",("supplied_structure_mapping_only",))

    def fingerprint(self,legacy_digest):
        records=sorted((g.record() for g in self.grants),key=lambda x:json.dumps(x,sort_keys=True))
        data={"profile":PROFILE,"legacy_policy_sha256":legacy_digest,"grants":records}
        return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
