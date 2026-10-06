"""Synthetic owner fixture records, in Research's own installed interpreter only."""
import json
import os
import sys
from pathlib import Path

from amphora_contracts_evaluation_reuse import ReuseProfile
from amphora_contracts_research import CandidateRevision, EligibilityProfile, SynthesisProfile, RouteOptionRecord
from amphora_research.eligibility import wire as eligibility_wire
from amphora_research.eligibility.store import EligibilityStore
from amphora_research.evaluation_reuse.profile import ConfiguredReuse
from amphora_research.persistence.ledger import IdentityLedger
from amphora_research.synthesis import wire as synthesis_wire
from amphora_research.synthesis.store import SynthesisStore
from sqlalchemy import create_engine


def prepare(case, engine):
    profile=ConfiguredReuse(ReuseProfile.model_validate_json(json.dumps(case['profile'])))
    scope=profile.record.scope
    ledger=IdentityLedger(engine)
    for value in (case['source_candidate'],case['target_candidate']):
        candidate=CandidateRevision.model_validate_json(json.dumps(value))
        ledger.publish(scope,candidate)
    decisions={}
    for name,conditions in case['conditions'].items():
        evaluation=profile.record.evaluation
        context={'subject':{'candidate':case['target_candidate']['reference'],'material_state':None,'sample':None},
                 'domain':'fixture.'+case['kind'],'purpose':evaluation.purpose,'conditions':conditions}
        ep=EligibilityProfile.model_validate_json(json.dumps({'wire_version':'1','authority':'synthetic',
            'reference':evaluation.method.applicability.model_dump(mode='json'),'context':context,
            'requirements':[{'criterion_id':'accuracy','kind':'model','method':evaluation.method.method.model_dump(mode='json'),
                             'required':False,'excluded_flags':[]}]}))
        # Deliberately exploratory: unknown optional accuracy remains focus.
        eligible=EligibilityStore(engine).assess(eligibility_wire.profile_from_wire(ep),(),
            'admin',case['kind']+'-'+name+'-eligibility')
        synthesis_context={'candidate':case['target_candidate']['reference'],'domain':context['domain'],
            'purpose':evaluation.purpose,'conditions':conditions,'scale':None,'purity':None}
        sp=SynthesisProfile.model_validate_json(json.dumps({'wire_version':'1','authority':'synthetic',
            'reference':evaluation.synthesis_policy.model_dump(mode='json'),'context':synthesis_context,
            'allowed_postures':['demonstrated'],'allowed_step_postures':['demonstrated'],'required_checks':['equipment']}))
        option=RouteOptionRecord.model_validate_json(json.dumps({'evidence':{'context':synthesis_context,
            'route':None,'posture':'unassessed','provenance':{'method':evaluation.method.method.model_dump(mode='json'),
                'tool':evaluation.synthesis_policy.model_dump(mode='json'),'models':[],'sources':[conditions]},
            'steps':[],'search':None,'next_checks':['assess_route']},'checks':[]}))
        synthesis=SynthesisStore(engine).assess(synthesis_wire.profile_from_wire(sp),
            (synthesis_wire.option_from_wire(option),),'admin',case['kind']+'-'+name+'-synthesis')
        decisions[name]={'eligibility':eligible.reference.model_dump(mode='json'),'synthesis':synthesis.reference.model_dump(mode='json')}
    return {'profile':profile.record.model_dump(mode='json'),'profile_ref':profile.reference.model_dump(mode='json'),'decisions':decisions}


if __name__=='__main__':
    config=json.loads(Path(sys.argv[1]).read_bytes())
    engine=create_engine(os.environ['AMPHORA_RESEARCH_DATABASE_URL'])
    try:print(json.dumps({case['kind']:prepare(case,engine) for case in config}))
    finally:engine.dispose()
