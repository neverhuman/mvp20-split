"""Public draft admission and cold reconstruction after removing the current grant."""
import json

def prepare(e, kind):
    # Environment supplies its public HTTP helper, no implementation imports.
    from_helper=e.public_http
    route='/v1/definition-drafts'
    definition=json.loads((e.root/(kind+'-graph.json')).read_bytes())
    saved=from_helper.decoded(e.runtime.endpoint,route+'/save',e.tokens['admin'],
        e.command('definition.save',{'draft_id':'structure','expected_revision':0,'title':'Supplied finite structure','definition':definition}))
    assert saved['outcome']['status']=='accepted'
    draft=from_helper.decoded(e.runtime.endpoint,route+'/structure',e.tokens['admin'])
    receipt=from_helper.decoded(e.runtime.endpoint,route+'/validate',e.tokens['admin'],
        e.command('definition.validate',{'draft_id':'structure','revision':1,'content_sha256':draft['head']['content_sha256']}))
    assert receipt['outcome']['status']=='accepted'
    validation=from_helper.decoded(e.runtime.endpoint,'/v1/definition-validations/'+receipt['outcome']['committed']['object_id'],e.tokens['admin'])
    assert validation['structurally_valid'] and validation['plan_sha256']==e.plans['candidate-'+kind]['sha256']
    e.resolve_chemical(kind) # Refresh capacity immediately before Runtime's own observation.
    e.draft_validation=validation
    return {key:validation[key] for key in ('draft_id','revision','content_sha256','validation_id','universe_sha256')}

def replace_without_grant(e, admission_command, admission_receipt, graph):
    http=e.public_http
    old=e.runtime;old.close()
    config=json.loads(open(old.config,encoding='utf-8').read())
    definition={'schema_version':'4','profile':'deterministic-v3','campaign_id':'profile-removed','revision':1,
        'scope':e.scope,'body':{'nodes':[{'kind':'finish','node_id':'done','outputs':[]}]}}
    (e.root/'profile-removed.json').write_text(json.dumps(definition),encoding='utf-8')
    config['graphs']=[{'definition':'profile-removed.json','releases':[],'schemas':[]}]
    config['tools']=[]
    from pathlib import Path
    Path(old.config).write_text(json.dumps(config),encoding='utf-8')
    e.runtime=http.Service(old.python,old.module,old.config,old.env,e.root,old.port)
    e.resources.append(e.runtime);e.runtime.ready(e.tokens['admin'],'/health')
    assert http.decoded(e.runtime.endpoint,'/v1/graph-runs/drafts',e.tokens['admin'],admission_command)==admission_receipt
    assert e.graph()==graph
    validation=http.decoded(e.runtime.endpoint,'/v1/definition-validations/'+e.draft_validation['validation_id'],e.tokens['admin'])
    assert validation==e.draft_validation
    rejected=http.decoded(e.runtime.endpoint,'/v1/graph-runs/drafts',e.tokens['admin'],e.command('graph.admit_draft',admission_command['payload']))
    assert rejected['outcome']['status']=='rejected' and rejected['outcome']['reason_code']=='draft_universe_changed'
    (e.root/'draft-replacement.json').write_text(json.dumps({'validation':validation,'admission':admission_receipt,'rejected_new_admission':rejected,'replay_identical':True,'completed_history_identical':True},indent=2)+'\n',encoding='utf-8')
