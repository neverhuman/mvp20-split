"""Installed Planning replay and offline token rebalance; never loads a key."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from amphora_agent_planning.campaign_packet_profiles import reviewed_instructions
from amphora_agent_planning.campaign_context.records import canonical
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.curation_input import CurationEnvelope, curation_tokenizer_reference
from amphora_agent_planning.curation_output import CurationOutput
from amphora_agent_planning.curation_budget.policy import CurationAllowance
from amphora_contracts_campaign_curation import campaign_curation_draft_schema
from amphora_contracts_core import Scope


def request(packet):
    value=packet['untrusted_context']['request']
    return RequestSnapshot.from_bytes(canonical(value),actor_id=value['actor_id'],
        scope=Scope.model_validate_json(json.dumps(value['reference']['scope'])))


def main(root,output):
    assert all(importlib.util.find_spec(name) is None for name in
        ('amphora_deployment','amphora_campaign_runtime','amphora_data_artifacts'))
    cases=[('curation-live-20261012a','supported',False),('curation-live-20261012a','missing',False),
        ('curation-live-v2-20261012a','supported',False),('curation-live-v2-20261012a','missing',True),
        ('curation-live-v3-20261012a','supported',False),('curation-live-diagnosis-20261012a','supported',False),
        ('curation-live-direct-20261012a','supported',False),('curation-live-extended-20261012a','supported',False),
        ('curation-live-compatible-20261012a','supported',True),('curation-live-semantics-20261012a','supported',True),
        ('curation-live-reasoning-20261012a','supported',True),('curation-live-feedback-20261012a','supported',True),
        ('curation-live-feedback-20261012b','supported',True),('curation-live-medium-20261012a','supported',True),
        ('curation-demo-live-browser-20261012a','',False)]
    replays=[]
    for folder,scenario,accepted in cases:
        path=root/folder/scenario;raw=(path/'original-packet.json').read_bytes();packet=json.loads(raw)
        original=request(packet);envelope=CurationEnvelope.bind(original,raw)
        assert envelope.body==(path/'original-envelope.json').read_bytes()
        try:CurationOutput.parse((path/'original-output.json').read_bytes(),original)
        except ValueError:assert not accepted
        else:assert accepted
        replays.append({'path':str(path),'envelope_sha256':envelope.sha256,'acceptance_unchanged':True})
    # Last replay is the actual scientific campaign with selected Knowledge/Research.
    baseline=json.loads(envelope.body)
    value=packet['untrusted_context']['request']
    value['context']['model']['tokenizer']=curation_tokenizer_reference('10').model_dump(mode='json')
    value['context']['limits'].update(max_input_tokens=196608,max_output_tokens=16384,total_tokens=212992)
    candidate=request(packet);new=CurationEnvelope.bind(candidate,canonical(packet));body=json.loads(new.body)
    assert new.input_bound<=196608
    assert body['reasoning']==baseline['reasoning']=={'effort':'medium'}
    assert body['text']==baseline['text'] and body['instructions']==baseline['instructions']
    assert reviewed_instructions('curation','10')==reviewed_instructions('curation','9')
    cost=CurationAllowance.cost(candidate.document().context.model,candidate.document().context.limits)
    assert cost==221184000 and cost<=250000000
    material={'status':'passed','provider_calls':0,'replays':replays,'offline_scientific_input_bound':new.input_bound,
        'maximum_cost_units':cost,'reservation_units':250000000,'instructions':body['instructions'],
        'tokenizer':curation_tokenizer_reference('10').model_dump(mode='json'),
        'output_schema':campaign_curation_draft_schema().model_dump(mode='json'),
        'limits':value['context']['limits'],'original_output_sha256':hashlib.sha256((path/'original-output.json').read_bytes()).hexdigest(),
        'limitations':['Offline fit only; new declaration/model artifact and actual provider acceptance still required']}
    assert not output.exists();output.write_text(json.dumps(material,indent=2)+'\n')
    print('Fifteen original replays unchanged; actual scientific context fits v10 within original reservation',flush=True)


if __name__=='__main__':main(*map(Path,sys.argv[1:]))
