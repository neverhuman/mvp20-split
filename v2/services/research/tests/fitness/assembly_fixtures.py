"""Pure fixtures computed by the existing Research owners; no storage/producer claim."""
import json
from dataclasses import replace
from pathlib import Path

from amphora_contracts_evaluation_identity import EvaluationIdentityInput, EvaluationReusePolicy
from amphora_contracts_research import AssessObservationUseRequest, CandidateRevision
from amphora_research.candidate_registration.profiles import schema_reference
from amphora_research.eligibility.decision import prepare as eligibility_decision
from amphora_research.experiments import wire as experiment_wire
from amphora_research.fitness.assembly import FitnessAssembly
from amphora_research.fitness.evidence import FitnessEvidence
from amphora_research.fitness.policy import FitnessPolicy, UNCERTAINTY
from amphora_research.fitness.reuse import EvaluationKey
from amphora_research.observations import wire as observation_wire
from amphora_research.observations.interpretation.document import InterpretationDocument
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.values import NumericValue
from amphora_research.synthesis.decision import prepare as synthesis_decision

from ..eligibility import test_policy as eligibility
from ..synthesis import test_policy as synthesis
from ..experiments.fixtures import experiment
from ..material_state.test_context import CANDIDATE, SCOPE, artifact, q
from ..observations.quality.test_policy import policy as use_policy
from ..observations.test_matching import observation


def inputs(value='1.25', *, measurement=None, synthesis_required=False, synthesis_status='unknown',
           eligibility_status='supported', rows=None, normalization=None, unit='mg/L', strict=False,
           plan_transform=None, directions=None):
    plan = experiment(unit=unit)
    if plan_transform is not None:
        plan = plan_transform(plan)
    record = observation(plan, measurement if measurement is not None else NumericValue(q(value, unit)))
    observations = rows(plan, record) if rows is not None else (record,)
    use = InterpretationProfile(SCOPE, use_policy(strict, normalization))
    request = AssessObservationUseRequest(wire_version='1', kind='observation-use', interpretation_id='fitness-use',
        profile=use.reference, experiment=experiment_wire.reference_to_wire(plan.identity.reference),
        observations=tuple(observation_wire.reference_to_wire(row.identity.reference) for row in observations))
    interpreted = InterpretationDocument.prepare(use, request, 'fixture', observations, plan).record
    ep = eligibility.policy()
    ed = eligibility_decision(ep, (eligibility.claim(disposition=eligibility_status),), 'fixture', 'fitness-eligibility').record
    sp = synthesis.policy()
    sp = replace(sp, context=replace(sp.context, purpose=ep.context.purpose))
    option = synthesis.option(status=synthesis_status)
    option = replace(option, evidence=replace(option.evidence, context=sp.context))
    sd = synthesis_decision(sp, (option,), 'fixture', 'fitness-synthesis').record
    source = artifact('candidate').model_copy(update={'schema_ref':schema_reference('candidate-space.polymer')})
    candidate = CandidateRevision(wire_version='1', reference=CANDIDATE, representation=source, supersedes=None)
    payload = json.loads((Path(__file__).parent/'fixtures/input.json').read_bytes())
    evaluation = payload['policy']
    evaluation['purpose'] = ep.context.purpose
    evaluation['method']['method'] = plan.protocol.method.model_dump(mode='json')
    evaluation['method']['applicability'] = ep.reference.model_dump(mode='json')
    evaluation['synthesis_policy'] = sp.reference.model_dump(mode='json')
    evaluation['objectives'] = [dict(evaluation['objectives'][0], objective_id=item.readout.criterion_id, unit=unit,
                                    direction=(directions or {}).get(item.readout.criterion_id,'minimize'),
                                    uncertainty_policy=UNCERTAINTY.model_dump(mode='json')) for item in plan.expectations]
    evaluation['required_context'] = ['conditions', 'experiment-applicability']
    policy = FitnessPolicy.prepare(EvaluationReusePolicy.model_validate_json(json.dumps(evaluation)), use.policy.reference, synthesis_required)
    payload['policy'] = policy.evaluation.model_dump(mode='json')
    payload['representation'].update(scope=SCOPE.model_dump(mode='json'), source=source.model_dump(mode='json'))
    payload['context'] = {'scope':SCOPE.model_dump(mode='json'), 'material_state':plan.samples[0].sample.record.material_state.model_dump(mode='json'),
        'inputs':[{'name':name, 'artifact':ref.model_dump(mode='json')} for name,ref in
                  [('conditions', ep.context.conditions), ('experiment-applicability', plan.protocol.applicability)]]}
    key = EvaluationKey(EvaluationIdentityInput.model_validate_json(json.dumps(payload)))
    return policy, key, FitnessEvidence(candidate, interpreted, ed, sd)


def assembly(*args, **kwargs):
    return FitnessAssembly.prepare(*inputs(*args, **kwargs))
