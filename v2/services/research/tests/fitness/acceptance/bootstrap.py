"""Research-owned synthetic setup in an isolated installed owner; no peer SQL/imports."""
import json
import os
import sys
from pathlib import Path

from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_fitness import FitnessEvidenceRecord, FitnessProfile
from amphora_contracts_research import AssessObservationUseRequest
from amphora_research.eligibility import wire as eligibility_wire
from amphora_research.eligibility.store import EligibilityStore
from amphora_research.experiments.store import ExperimentStore
from amphora_research.fitness.policy import FitnessPolicy
from amphora_research.fitness.profile import ConfiguredFitness
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.interpretation.store import InterpretationStore
from amphora_research.observations.store import ObservationStore
from amphora_research.persistence.ledger import IdentityLedger
from amphora_research.synthesis import wire as synthesis_wire
from amphora_research.synthesis.store import SynthesisStore
from sqlalchemy import create_engine


def setup(payload):
    evidence = FitnessEvidenceRecord.model_validate_json(json.dumps(payload['evidence']))
    declared = EvaluationIdentityInput.model_validate_json(json.dumps(payload['identity']))
    scope,actor = evidence.candidate.reference.scope,'fixture'
    engine = create_engine(os.environ['AMPHORA_RESEARCH_DATABASE_URL'])
    try:
        ledger = IdentityLedger(engine)
        ledger.publish(scope,evidence.candidate)
        plan = evidence.interpretation.experiment
        specimen = plan.samples[0]
        MaterialStateStore(engine).publish(scope,actor,specimen.state)
        ledger.publish(scope,specimen.sample)
        ExperimentStore(engine).publish(scope,actor,plan)
        row = evidence.interpretation.reviews[0].observation
        ObservationStore(engine).publish(scope,actor,row)
        profile = InterpretationProfile.from_wire(evidence.interpretation.profile)
        request = AssessObservationUseRequest(wire_version='1',kind='observation-use',interpretation_id='fitness-use',
            profile=profile.reference,experiment=plan.reference,observations=(row.reference,))
        store = InterpretationStore(engine)
        prepared = store.prepare(store.begin(profile,request,actor).intent)
        interpreted = store.complete(prepared,prepared.sources).result
        assessment = evidence.eligibility.assessment
        claim = assessment.reviews[0].claim
        claim = claim.model_copy(update={'origin':claim.origin.model_copy(update={'source':row.source,'observation':row.reference})})
        eligibility = EligibilityStore(engine).assess(eligibility_wire.profile_from_wire(assessment.policy),
            (eligibility_wire.claim_from_wire(claim),),actor,'fitness-eligibility')
        assessment = evidence.synthesis.assessment
        synthesis = SynthesisStore(engine).assess(synthesis_wire.profile_from_wire(assessment.policy),
            tuple(synthesis_wire.option_from_wire(item.option) for item in assessment.alternatives),actor,'fitness-synthesis')
        policy = FitnessPolicy.prepare(declared.policy,profile.policy.reference,False)
        declared = declared.model_copy(update={'policy':policy.evaluation})
        configured = ConfiguredFitness(FitnessProfile(wire_version='1',authority='synthetic',scope=scope,
            evaluation=policy.evaluation,observation_use=policy.observation_use,synthesis_required=False))
        return {'profile':configured.record.model_dump(mode='json'),'identity':declared.model_dump(mode='json'),
            'request':{'wire_version':'1','fitness_id':'fitness-http','profile':configured.reference.model_dump(mode='json'),
                **{name:record.reference.model_dump(mode='json') for name,record in
                   [('candidate',evidence.candidate),('interpretation',interpreted),('eligibility',eligibility),('synthesis',synthesis)]}}}
    finally:
        engine.dispose()


if __name__ == '__main__':
    print(json.dumps(setup(json.loads(Path(sys.argv[1]).read_bytes()))))
