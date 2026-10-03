"""Material identity binds exact design revision, preparation and attributable features."""
from dataclasses import dataclass

from amphora_contracts_research import CandidateRevisionRef, MaterialStateRevisionRef

from .features import MaterialFeature
from .preparation import PreparationHistory
from .validation import bounded_tuple, require


@dataclass(frozen=True, slots=True)
class StateIdentity:
    reference: MaterialStateRevisionRef
    candidate: CandidateRevisionRef
    supersedes: MaterialStateRevisionRef | None

    def __post_init__(self):
        require(type(self.reference) is MaterialStateRevisionRef and type(self.candidate) is CandidateRevisionRef,"state_reference_required")
        require(self.reference.scope == self.candidate.scope,"state_candidate_scope_mismatch")
        prior = self.supersedes
        if prior is None:
            require(self.reference.revision == 1,"state_predecessor_required")
        else:
            require(type(prior) is MaterialStateRevisionRef,"state_predecessor_type")
            require(prior.scope == self.reference.scope and prior.material_state_id == self.reference.material_state_id
                    and prior.revision + 1 == self.reference.revision,"state_predecessor_mismatch")


@dataclass(frozen=True, slots=True)
class MaterialState:
    identity: StateIdentity
    preparation: PreparationHistory
    features: tuple[MaterialFeature, ...]

    def __post_init__(self):
        require(type(self.identity) is StateIdentity,"state_identity_required")
        require(type(self.preparation) is PreparationHistory,"preparation_history_required")
        bounded_tuple(self.features,128,"material_feature_bound")
        require(all(type(item) is MaterialFeature for item in self.features),"material_feature_required")
        require(len({item.name for item in self.features}) == len(self.features),"duplicate_material_feature")
        scope = self.identity.reference.scope
        sources = [item.attribution.source for item in self.preparation.events]
        sources += [item.evidence.source for item in self.features if item.evidence.source is not None]
        require(all(source.scope == scope for source in sources),"material_source_scope_mismatch")
