"""Source-reviewed seed-only worker I/O envelope; no latency/throughput prediction."""
from dataclasses import dataclass

from amphora_contracts_population import BirthPage,MembershipPage,EvaluationSlotPage

from ..ranking import require
from .pages import PageEnvelope
from .publications import NumericPublicationProfile
from .work import add,multiply,ScopeWork


REVIEWED_SDK_RELEASE="0.4.0"


@dataclass(frozen=True)
class ValidationIo:
    artifact_reads: int
    content_read_bytes: int
    data_requests: int
    runtime_requests: int

    def __post_init__(self):
        for value in (self.artifact_reads,self.content_read_bytes,self.data_requests,self.runtime_requests):
            add(value,0)

    def include(self,other,factor=1):
        require(type(other) is ValidationIo,"composition_validation_io")
        return ValidationIo(*(add(left,multiply(right,factor)) for left,right in zip(
            (self.artifact_reads,self.content_read_bytes,self.data_requests,self.runtime_requests),
            (other.artifact_reads,other.content_read_bytes,other.data_requests,other.runtime_requests),strict=True)))

    @property
    def response_body_bytes(self):
        # SDK0.4 defaults to262144 and reads one extra byte to detect oversized replies.
        # Includes body bytes only, not HTTP headers or transport framing.
        return multiply(add(self.data_requests,self.runtime_requests),262145)


class SeedValidationIoProfile:
    """Seed/slice/numeric-method kernels in generation0 only, including SDK recovery.

    Excludes Runtime-owned graph binding work, worker polling, owner SQL/CPU and
    retention confirmation by operators. Unknown operations and successors reject.
    Byte caps bound accepted inputs; oversized-input/transport failures stop early.
    """
    def __init__(self,specification,image_sha256):
        self.publications=NumericPublicationProfile(specification,image_sha256)
        record=self.publications.original.record
        require(record.budget.successor_generations==0,"composition_validation_successor_profile")
        n=record.budget.population_size
        page=lambda model,rows:PageEnvelope.population(model).bound(rows).pages
        cohort=page(MembershipPage,n)
        slots=page(EvaluationSlotPage,n*len(record.method_graph.methods))
        births=page(BirthPage,n)
        # Each tuple separates non-page reads and bounded page reads.
        self._reads={"seed":(2,0),"slice":(6,cohort+slots+births),
            "evaluate-squares":(5,cohort+slots),"evaluate-negative-sum":(5,cohort+slots)}

    def per_attempt(self,binding):
        publications=self.publications.per_call(binding)
        operation=binding.capability_id.removeprefix("numeric.population-")
        require(operation in self._reads,"composition_unknown_validation_profile")
        fixed,pages=self._reads[operation]
        reads=add(fixed,pages)
        content=add(multiply(fixed,262144),multiply(pages,131072))
        # A command exchange has <=3 POSTs +2 recovery GETs. Refresh has
        # one such renewal plus one run snapshot; streaming is never retried.
        data=add(multiply(reads,2),multiply(publications,11))
        # Up to claim5 + complete5 + two refreshes12 on the failure path,
        # plus each read's refresh6 and every publication's three refreshes18.
        runtime=add(22,add(multiply(reads,6),multiply(publications,18)))
        return ValidationIo(reads,content,data,runtime)

    def assess(self,work,max_attempts_per_activation):
        require(type(work) is ScopeWork,"composition_work_shape")
        require(type(max_attempts_per_activation) is int and 1<=max_attempts_per_activation<=100,
            "composition_validation_attempts")
        result=ValidationIo(0,0,0,0)
        for binding,count in work.calls:
            result=result.include(self.per_attempt(binding),multiply(count,max_attempts_per_activation))
        return result
