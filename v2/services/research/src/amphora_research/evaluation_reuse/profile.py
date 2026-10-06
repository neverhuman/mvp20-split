from dataclasses import dataclass

from amphora_contracts_evaluation_reuse import ReuseProfile, ReuseProfileRef

from .errors import require
from .policy import ReusePolicy


@dataclass(frozen=True, slots=True)
class ConfiguredReuse:
    record: ReuseProfile

    def __post_init__(self):
        object.__setattr__(self, 'record', ReuseProfile.model_validate_json(self.record.model_dump_json()))
        self.policy

    @property
    def policy(self):
        r = self.record
        return ReusePolicy(r.scope,r.evaluation,r.canonicalizer,r.synthesis_required)

    @property
    def reference(self):
        return ReuseProfileRef(scope=self.record.scope,policy=self.policy.reference)

    def bind(self, request):
        require(request.profile == self.reference, 'reuse_profile_mismatch')
        require(all(ref.scope == self.record.scope for ref in (request.source.candidate,request.source.identity,
            request.source.canonicalization,request.target.candidate,request.target.identity,
            request.target.canonicalization,request.evaluation,request.eligibility,request.synthesis)), 'reuse_request_scope_mismatch')
        require(request.eligibility.kind == 'eligibility' and request.synthesis.kind == 'synthesis', 'reuse_request_kind_mismatch')
        return request
