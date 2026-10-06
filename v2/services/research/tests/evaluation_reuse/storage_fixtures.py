"""Real owner SQL, scripted public producer/Data evidence; not a live-peer proof."""
from dataclasses import replace

from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_evaluation_reuse import ProducerRef, ReuseCandidateInput, ReuseProfile, ReuseRequest
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt
from amphora_research.eligibility import wire as eligibility_wire
from amphora_research.eligibility.store import EligibilityStore
from amphora_research.evaluation_reuse.operations import ReuseOperations
from amphora_research.evaluation_reuse.profile import ConfiguredReuse
from amphora_research.synthesis import wire as synthesis_wire
from amphora_research.synthesis.store import SynthesisStore
from amphora_research.transport.access import Principal

from ..material_state.storage_fixtures import in_scope
from .fixtures import Data, producer
from .policy_fixtures import bundle


class Sources(Data):
    def __init__(self):
        super().__init__()
        self.error = None

    def read(self, reference):
        self.calls.append(reference)
        if self.error is not None:
            raise self.error
        return self.contents.get(reference.artifact_id,b'{}')


class Runtime:
    def __init__(self):
        self.proofs = {}
        self.calls = []
        self.error = None

    def add(self, proof, name):
        proof=proof.model_copy(update={'completion':proof.completion.model_copy(update={'completion_id':name})})
        reference=ProducerRef(scope=proof.completion.scope,run_id=proof.completion.run_id,completion_id=name)
        self.proofs[name]=proof
        return reference

    def read(self, selection):
        self.calls.append(selection)
        if self.error is not None:
            raise self.error
        return self.proofs[selection.completion_id]


def stored_case(ledger, *, different_context=False):
    identities,scope=ledger
    policy,source,target,subjects,*_=bundle(different_context=different_context)
    source,target=in_scope(source.record,scope),in_scope(target.record,scope)
    source_candidate,target_candidate=in_scope(subjects.source,scope),in_scope(subjects.target,scope)
    identities.publish(scope,source_candidate);identities.publish(scope,target_candidate)
    ea=in_scope(subjects.eligibility.assessment,scope)
    claims=tuple(row.claim.model_copy(update={'origin':row.claim.origin.model_copy(update={'observation':None})}) for row in ea.reviews)
    ed=EligibilityStore(identities.engine).assess(eligibility_wire.profile_from_wire(ea.policy),
        tuple(eligibility_wire.claim_from_wire(claim) for claim in claims),'fixture','reuse-eligibility')
    sa=in_scope(subjects.synthesis.assessment,scope)
    sd=SynthesisStore(identities.engine).assess(synthesis_wire.profile_from_wire(sa.policy),
        tuple(synthesis_wire.option_from_wire(row.option) for row in sa.alternatives),'fixture','reuse-synthesis')
    configured=ConfiguredReuse(ReuseProfile(wire_version='1',authority='synthetic',scope=scope,
        evaluation=source.policy,canonicalizer=policy.canonicalizer,synthesis_required=policy.synthesis_required))
    data,runtime=Sources(),Runtime();selected=[]
    for name,declared,candidate,raw in [('source',source,source_candidate,b'{"fixture":1}'),('target',target,target_candidate,b'{ "fixture":1 }')]:
        data.contents[candidate.representation.artifact_id]=raw
        receipt=CanonicalCandidate(wire_version='1',authority='synthetic_encoding',scope=scope,kind=declared.representation.policy.kind,
            semantic_profile=declared.representation.policy.semantic_profile,equivalence_profile=declared.representation.policy.equivalence_profile,
            source_sha256=candidate.representation.sha256,canonical_sha256=declared.representation.canonical_sha256)
        output=data.add(scope,name+'-canonical',receipt.model_dump(mode='json'),CanonicalCandidate,'candidate-canonicalization.receipt')
        reference=runtime.add(producer(candidate.representation,output,policy.canonicalizer),name+'-canonical')
        identity=data.add(scope,name+'-identity',declared.model_dump(mode='json'),EvaluationIdentityInput,'evaluation-identity.input')
        selected.append(ReuseCandidateInput(candidate=candidate.reference,identity=identity,canonicalization=reference))
    result=SyntheticEvaluationReceipt(wire_version='1',authority='synthetic_evaluation',scope=scope,
        input_sha256=selected[0].identity.sha256,canonical_sha256=source.representation.canonical_sha256,
        method=source.policy.method,objective_id='synthetic-digest-score',unit='1',value=13421772)
    output=data.add(scope,'evaluation',result.model_dump(mode='json'),SyntheticEvaluationReceipt,'synthetic-evaluation.receipt')
    reference=runtime.add(producer(selected[0].identity,output,source.policy.method.evaluator),'evaluate')
    request=ReuseRequest(wire_version='1',reuse_id='reuse-1',profile=configured.reference,source=selected[0],target=selected[1],
        evaluation=reference,eligibility=ed.reference,synthesis=sd.reference)
    principal=Principal('fixture',scope,frozenset({'qualify_evaluation_reuse','read_evaluation_reuse','read_candidate','read_scientific_record'}))
    operations=ReuseOperations(identities,(configured,),lambda _:data,lambda _:runtime)
    return operations,principal,request,data,runtime
