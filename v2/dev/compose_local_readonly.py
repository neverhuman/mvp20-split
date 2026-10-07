"""Create immutable, nonsecret local infrastructure configuration; no campaign admission."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from amphora_deployment.installation import SERVING_HOSTS
from amphora_deployment.lifecycle.routes import Routes
from check_boundaries import project_specs


def compose(output, registry_evidence=False):
    output = output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    root = Path(os.environ['LOCALAPPDATA']) / 'Amphora/local-v2/installation'
    routes = Routes.load(root)
    scope = {'tenant_id': 'internal', 'project_id': 'demo'}
    def write(name, value):
        path = output / name
        path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
        return path
    def principal(owner, actions):
        return {'token_env': 'AMPHORA_'+owner.upper()+'_OPERATOR_TOKEN',
                'actor_id': 'operator', 'scope': scope, 'actions': actions}
    def peer(owner, reference):
        return {'endpoint': routes.endpoint(owner), 'token_env': 'AMPHORA_'+reference}
    schema = Path('v2/contracts/schemas/v1/core.artifact-ref.validation.json').read_bytes()
    schema_path = output / 'artifact-ref.schema.json'
    schema_path.write_bytes(schema)
    artifact_root = root.parent / 'artifacts'
    artifact_root.mkdir(exist_ok=True)
    configs = {
        'runtime': {'principals':[principal('runtime',['read'])],
                    'fixtures':[json.loads(Path('v2/services/campaign_runtime/tests/fixtures/prepared-run.json').read_bytes())['payload']],
                    'inspection':{'cursor_key_env':'AMPHORA_CURSOR_KEY','ttl_seconds':900}},
        'artifact': {'principals':[principal('artifact',['read'])], 'storage_root':str(artifact_root),
                     'profiles':[{'media_type':'application/json','schema_id':'core.artifact-ref','version':'1',
                                  'sha256':hashlib.sha256(schema).hexdigest(),'schema_path':str(schema_path)}]},
        'registry': {'principals':[principal('registry',['read'])], 'resources':{
            'architecture':'x86_64','operating_system':'windows','cpu_millicores':2000,'memory_mib':4096,
            'gpu_count':0,'timeout_seconds':60,'max_parallel_invocations':1,'max_batch_size':16}},
        'research': {'principals':[principal('research',['resolve_identity','read_declarations'])]},
        'knowledge': {'principals':[principal('knowledge',['read_graph'])],
                      'vocabulary':json.loads(Path('v2/services/knowledge/tests/fixtures/initial.json').read_bytes())['vocabulary'],
                      'policy':{'policy_id':'synthetic-structural','version':'1','authority':'structural_only',
                                'max_entities':4096,'max_assertions':8192,'max_aliases':4096,'max_retractions':8192},
                      'data':peer('artifact','KNOWLEDGE_DATA_TOKEN'),
                      'research':peer('research','KNOWLEDGE_RESEARCH_TOKEN')},
        'planning': {'principals':[principal('planning',['read_attempts'])]},
        'gateway': {'profile':'local-gateway-v1','public_directory':str(Path('v2/studio/dist/local').absolute()),
                    'peers':{owner:peer(owner,owner.upper()+'_OPERATOR_TOKEN') for owner in SERVING_HOSTS if owner!='gateway'},
                    'context':{'actor_id':'operator','scope':scope,'run_id':None,'synthetic':True},
                    'launcher_key_env':'AMPHORA_GATEWAY_SESSION_KEY'}
    }
    specs = {cfg['project']['name']:path for path,cfg,_ in project_specs()}
    if registry_evidence:
        # Only dormant synthetic descriptor registration; never activate/deploy.
        configs['registry']['principals'][0]['actions'].append('register')
    owners = {}
    for owner, recipe in SERVING_HOSTS.items():
        configuration = configs[owner]
        references = [owner.upper()+'_OPERATOR_TOKEN']
        if owner not in ('planning','gateway'):
            configuration['database_url_env'] = recipe.database_environment
        if owner=='runtime': references += ['CURSOR_KEY']
        if owner=='knowledge': references += ['KNOWLEDGE_DATA_TOKEN','KNOWLEDGE_RESEARCH_TOKEN']
        if owner=='gateway': references = ['GATEWAY_SESSION_KEY']+[name.upper()+'_OPERATOR_TOKEN' for name in SERVING_HOSTS if name!='gateway']
        installation = Path('.test-results/local-owner-inventory-20261006a/owners')/owner
        if owner=='planning': installation = Path('.test-results/local-planning-role-20261006a')
        if owner=='gateway': installation = Path('.test-results/local-gateway-drain-20261006a')
        owners[owner] = {'installation':str(installation.absolute()), 'source_lock':str(specs[recipe.package]/'uv.lock'),
                         'configuration':str(write(owner+'.json',configuration)), 'secret_references':references}
    manifest = write('manifest.json',{'profile':'local-supervisor-v1','owners':owners})
    write('scope.json',{'purpose':'Read-only infrastructure qualification', 'campaign_admission':False,
                       'scientific_tools_eligible':False,'provider_calls':False,'peer_workflows_configured':False,
                       'synthetic_registry_receipt_probe':registry_evidence})
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--registry-evidence',action='store_true')
    args=parser.parse_args()
    print(compose(args.output,args.registry_evidence))
