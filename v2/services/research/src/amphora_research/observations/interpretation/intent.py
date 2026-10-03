"""Pin original actor, request and full reviewed configuration before external work."""
import json
from dataclasses import dataclass

from amphora_contracts_research import (
    AssessObservationUseRequest,
    NormalizationProfile,
    NormalizeObservationRequest,
    ObservationUseProfile,
)

from ..identity import identifier, require
from .document import canonical
from .profiles import InterpretationProfile


@dataclass(frozen=True, slots=True)
class InterpretationIntent:
    profile: InterpretationProfile
    request: NormalizeObservationRequest | AssessObservationUseRequest
    actor: str
    content: bytes

    @classmethod
    def prepare(cls, profile, request, actor):
        profile = InterpretationProfile.from_wire(profile.to_wire())
        request = profile.bind(request)
        identifier(actor)
        content = canonical({"format":"research.interpretation-intent.v1","profile":profile.to_wire().model_dump(mode="json"),
            "request":request.model_dump(mode="json"),"actor":actor})
        require(len(content) <= 2097152,"interpretation_intent_byte_limit")
        return cls(profile,request,actor,content)

    @classmethod
    def restore(cls, content):
        raw = json.loads(content)
        require(raw["format"] == "research.interpretation-intent.v1","interpretation_intent_format")
        kind = raw["profile"]["kind"]
        require(kind in ("normalization","observation-use"),"interpretation_intent_kind")
        profile_model,request_model = ((NormalizationProfile,NormalizeObservationRequest) if kind == "normalization"
            else (ObservationUseProfile,AssessObservationUseRequest))
        profile = InterpretationProfile.from_wire(profile_model.model_validate_json(json.dumps(raw["profile"])))
        return cls.prepare(profile,request_model.model_validate_json(json.dumps(raw["request"])),raw["actor"])

    @property
    def key(self):
        scope = self.profile.scope
        return {"tenant":scope.tenant_id,"project":scope.project_id,"kind":self.profile.kind,"id":self.request.interpretation_id}
