import hashlib

from amphora_contracts_fitness import FitnessProfile, FitnessRequest
from amphora_contracts_research import AssessObservationUseRequest
from amphora_research.eligibility import wire as eligibility_wire
from amphora_research.eligibility.store import EligibilityStore
from amphora_research.experiments.store import ExperimentStore
from amphora_research.fitness.operations import FitnessOperations
from amphora_research.fitness.profile import ConfiguredFitness
from amphora_research.fitness.resolution import identity_schema
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.interpretation.store import InterpretationStore
from amphora_research.observations.store import ObservationStore
from amphora_research.synthesis import wire as synthesis_wire
from amphora_research.synthesis.store import SynthesisStore
from amphora_research.transport.access import Principal

from .assembly_fixtures import inputs
from ..material_state.storage_fixtures import in_scope


class Reader:
    """Scripted Data only; immutable owner records below use real PostgreSQL."""
    def __init__(self, source, raw):
        self.source, self.raw, self.calls, self.error = source, raw, [], None

    def read(self, reference):
        self.calls.append(reference)
        if self.error is not None:
            raise self.error
        return self.raw if reference == self.source else b'{}'


def stored_case(ledger):
    identities,scope = ledger
    policy,key,evidence = inputs()
    candidate = in_scope(evidence.candidate,scope)
    plan = in_scope(evidence.interpretation.experiment,scope)
    row = in_scope(evidence.interpretation.reviews[0].observation,scope)
    identities.publish(scope,candidate)
    MaterialStateStore(identities.engine).publish(scope,'fixture',plan.samples[0].state)
    identities.publish(scope,plan.samples[0].sample)
    ExperimentStore(identities.engine).publish(scope,'fixture',plan)
    ObservationStore(identities.engine).publish(scope,'fixture',row)
    use = InterpretationProfile.from_wire(in_scope(evidence.interpretation.profile,scope))
    request = AssessObservationUseRequest(wire_version='1',kind='observation-use',interpretation_id='fitness-use',
        profile=use.reference,experiment=plan.reference,observations=(row.reference,))
    store = InterpretationStore(identities.engine)
    prepared = store.prepare(store.begin(use,request,'fixture').intent)
    interpreted = store.complete(prepared,prepared.sources).result
    ea = in_scope(evidence.eligibility.assessment,scope)
    claim = ea.reviews[0].claim
    claim = claim.model_copy(update={'origin':claim.origin.model_copy(update={'source':row.source,'observation':row.reference})})
    ed = EligibilityStore(identities.engine).assess(eligibility_wire.profile_from_wire(ea.policy),
        (eligibility_wire.claim_from_wire(claim),),'fixture','fitness-eligibility')
    sa = in_scope(evidence.synthesis.assessment,scope)
    sd = SynthesisStore(identities.engine).assess(synthesis_wire.profile_from_wire(sa.policy),
        tuple(synthesis_wire.option_from_wire(item.option) for item in sa.alternatives),'fixture','fitness-synthesis')
    profile = ConfiguredFitness(FitnessProfile(wire_version='1',authority='synthetic',scope=scope,
        evaluation=policy.evaluation,observation_use=policy.observation_use,synthesis_required=policy.synthesis_required))
    declared = in_scope(key.record,scope)
    raw = declared.model_dump_json().encode()
    source = candidate.representation.model_copy(update={'artifact_id':'declared-key','schema_ref':identity_schema(),
        'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw)})
    request = FitnessRequest(wire_version='1',fitness_id='fitness-1',profile=profile.reference,candidate=candidate.reference,
        interpretation=interpreted.reference,eligibility=ed.reference,synthesis=sd.reference,declared_identity=source)
    reader = Reader(source,raw)
    principal = Principal('fixture',scope,frozenset({'assemble_fitness','read_fitness','read_candidate',
        'read_observation_interpretation','read_scientific_record'}))
    operations = FitnessOperations(identities,(profile,),lambda scope:reader)
    return operations,principal,request,reader
