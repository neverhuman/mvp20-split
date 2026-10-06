"""Actual installed Runtime/tool/Data/Research producer-backed synthetic reuse."""
import argparse
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import URL
from check_boundaries import ROOT
from install_owner_peer import install
from postgres_fixture import owned_state, research_owner, registry_owner


def verify(output, *, images=None, replacement=False):
    if os.environ.get('AMPHORA_TEST_POSTGRES') != '1':
        raise ValueError('Explicit owned PostgreSQL fixture opt-in required')
    state=owned_state();research_owner(state)
    output=output.absolute();output.mkdir(parents=True,exist_ok=False)
    packages={'runtime':'amphora-campaign-runtime','artifact':'amphora-data-artifacts','research':'amphora-research',
        'numeric':'amphora-numeric-space','polymer':'amphora-polymer-space','sequence':'amphora-sequence-space',
        'digest':'amphora-synthetic-digest','controller':'amphora-tool-protocol'}
    if images is not None:
        registry_owner(state)
        packages['registry']='amphora-capability-registry'
    modules=tuple(package.replace('-','_') for key,package in packages.items() if key!='controller')
    interpreters,manifests={},{}
    for name,package in packages.items():
        forbidden=tuple(module for module in modules if module != package.replace('-','_'))
        interpreters[name]=str(install(output/name,package,forbidden))
        manifests[name]=json.loads((output/name/'manifest.json').read_bytes())
    replacements={}
    if replacement:
        for name in ('runtime','research','numeric','polymer','sequence','digest'):
            target=output/(name+'-replacement')
            forbidden=tuple(module for module in modules if module != packages[name].replace('-','_'))
            replacements[name]=str(install(target,packages[name],forbidden))
            manifests[name+'-replacement']=json.loads((target/'manifest.json').read_bytes())
            assert manifests[name]['wheels']==manifests[name+'-replacement']['wheels']
    host,port=state['endpoint'].split(':')
    env={key:value for key,value in os.environ.items() if key.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','COMSPEC'}}
    for name in ('runtime','artifact','research') + (('registry',) if images is not None else ()):
        url=URL.create('postgresql+psycopg',username=name+'_service',password=state['password'],host=host,port=int(port),database=state['database'])
        env['AMPHORA_'+name.upper()+'_DATABASE_URL']=url.render_as_string(hide_password=False)
        migration_env=dict(env,**{'AMPHORA_'+name.upper()+'_MIGRATION_URL':url.set(username=name+'_migrator').render_as_string(hide_password=False)})
        result=subprocess.run([interpreters[name],'-I','-m',packages[name].replace('-','_')+'.persistence.migrate'],
            env=migration_env,cwd=output,capture_output=True,text=True,encoding='utf-8',timeout=60)
        (output/(name+'-migration.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Owned migration failed; inspect migration log')
    config={**interpreters,'images':None if images is None else str(images.absolute()),'replacements':replacements,'packages':manifests,'evidence':str(output/'http')}
    path=output/'acceptance.json';path.write_text(json.dumps(config),encoding='utf-8')
    result=subprocess.run([interpreters['controller'],'-I',str(ROOT/'services/research/tests/evaluation_reuse/acceptance/probe.py'),str(path)],
        env=env,cwd=output,capture_output=True,text=True,encoding='utf-8',timeout=600)
    (output/'probe.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Evaluation reuse handoff failed; inspect '+str(output/'probe.log'))
    report=json.loads(result.stdout)
    print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--images',type=Path);parser.add_argument('--replacement',action='store_true')
    args=parser.parse_args()
    verify(args.output,images=args.images,replacement=args.replacement)
