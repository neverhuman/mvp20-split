"""Reviewed response window; independent of spend, leases and retry authority."""
from dataclasses import dataclass
from ..context.policy import require
from ..curation_budget import ceiling
from ..curation_input import CurationInputBound


@dataclass(frozen=True)
class CurationResponseWindow:
    profile: str
    seconds: int

    @classmethod
    def bind(cls, profile, seconds, scope):
        require(profile in {'standard-v1','scientific-v1'}, 'curation_deadline_profile')
        maximum=60 if profile=='standard-v1' else 180
        require(type(seconds) is int and 1<=seconds<=maximum, 'curation_provider_timeout')
        if profile=='scientific-v1':
            require((scope.tenant_id,scope.project_id)==ceiling.REVIEWED_DEMO,'curation_deadline_scope')
        return cls(profile,seconds)

    @property
    def maximum(self):
        return 60 if self.profile=='standard-v1' else 180

    @property
    def transport_options(self):
        return {} if self.profile=='standard-v1' else {'timeout_profile':'curation-scientific-v1'}

    def require_model(self,model):
        if self.profile=='scientific-v1':
            require(CurationInputBound.bind(model).envelope_version=='10','curation_deadline_model')
