"""Reviewed numeric-worker publication count upper bounds, not full admission."""
from dataclasses import dataclass

from amphora_contracts_population import (BirthPage,MembershipPage,EvaluationSlotPage,
    EvaluationKeyPage,MethodObservationPage,FitnessPage,SelectionPage)
from amphora_contracts_tools import ToolBinding

from ..population.specification import OriginalPopulation
from ..ranking import require
from .pages import PageEnvelope
from .work import add,multiply,ScopeWork


REVIEWED_RELEASE="0.24.0"


def reference_groups(parents):
    require(type(parents) is int and parents>=0,"composition_root_parents")
    total=0
    while parents>120:
        parents=add(parents,119)//120
        total=add(total,parents)
    return total


@dataclass(frozen=True)
class PublicationBudget:
    successful_artifacts: int
    all_attempt_artifacts: int
    all_attempt_content_bytes: int

    def __post_init__(self):
        for value in (self.successful_artifacts,self.all_attempt_artifacts,self.all_attempt_content_bytes):add(value,0)
        require(self.all_attempt_artifacts>=self.successful_artifacts,"composition_publication_budget")


class NumericPublicationProfile:
    """All calls use full spec maxima; no speculative branch/duplicate pruning.

    Counts include reference groups; method output/record caps remain enforced by
    their workers. This does not establish row fitness, external ancestry, owner
    rights, receipt storage, validation I/O or a graph's execution authority.
    """
    def __init__(self,specification,image_sha256):
        self.original=OriginalPopulation(specification)
        self.image_sha256=ToolBinding(capability_id="numeric.population-seed",
            release=REVIEWED_RELEASE,image_sha256=image_sha256,
            contract_version="1").image_sha256
        n=self.original.record.budget.population_size
        methods=len(self.original.record.method_graph.methods)
        page=lambda model,rows:PageEnvelope.population(model).bound(rows).pages
        births=page(BirthPage,n);cohort=page(MembershipPage,n)
        slots=page(EvaluationSlotPage,n*methods)
        keys=page(EvaluationKeyPage,n*methods);observations=page(MethodObservationPage,n*methods)
        pool=page(MembershipPage,2*n);fitness=page(FitnessPage,2*n);selection=page(SelectionPage,2*n)
        preparation=n+births+cohort+slots+4+sum(reference_groups(k) for k in
            (1+births,1+cohort,2+slots))
        history=self.original.record.budget.successor_generations+1
        self._counts={
            "seed":preparation,
            "slice":min(n,self.original.record.budget.dispatch_slice)+1,
            "evaluate-squares":1,"evaluate-negative-sum":1,
            "collect-primary":n*methods+keys+observations+4+
                reference_groups(1+keys)+reference_groups(1+observations),
            "assemble-primary":pool+fitness+4+reference_groups(1+pool)+
                reference_groups(history+2+fitness),
            "select-primary":selection+4+reference_groups(3+selection),
            "prepare-successor":preparation+pool+4+reference_groups(2+pool),
            "prepare-successor-collection":1,"prepare-successor-slice":1,
            "prepare-successor-request":1,"prepare-selection":1}

    def per_call(self,binding):
        binding=ToolBinding.model_validate_json(binding.model_dump_json())
        prefix="numeric.population-"
        require(binding.capability_id.startswith(prefix),"composition_unknown_publication_profile")
        operation=binding.capability_id[len(prefix):]
        require(operation in self._counts,"composition_unknown_publication_profile")
        require(binding.release==REVIEWED_RELEASE
            and binding.image_sha256==self.image_sha256 and binding.contract_version=="1",
            "composition_publication_release_pin")
        count=self._counts[operation]
        require(count<=4096,"composition_attempt_publications")
        return count

    def assess(self,work,max_attempts_per_activation):
        require(type(work) is ScopeWork,"composition_work_shape")
        require(type(max_attempts_per_activation) is int and 1<=max_attempts_per_activation<=100,
            "composition_publication_attempts")
        count=work.bindings.materializations
        for binding,calls in work.calls:
            count=add(count,multiply(self.per_call(binding),calls))
        # Graph-owned materializations are not repeated as worker attempts.
        attempted=add(work.bindings.materializations,
            multiply(count-work.bindings.materializations,max_attempts_per_activation))
        content=add(multiply(attempted-work.bindings.materializations,262144),work.bindings.declared_bytes)
        return PublicationBudget(count,attempted,content)
