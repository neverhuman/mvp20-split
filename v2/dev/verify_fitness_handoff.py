"""Actual isolated Research/Data fitness projection; producer-backed reuse is a separate gate."""
import argparse
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import URL
from check_boundaries import ROOT
from install_owner_peer import install
from postgres_fixture import owned_state, research_owner


def verify(output):
    if os.environ.get('AMPHORA_TEST_POSTGRES') != '1':
        raise ValueError('Explicit owned PostgreSQL fixture opt-in required')
    state=owned_state();research_owner(state)
    output=output.absolute();output.mkdir(parents=True,exist_ok=False)
    packages={'artifact':'amphora-data-artifacts','research':'amphora-research','controller':'amphora-tool-protocol'}
    modules=('amphora_data_artifacts','amphora_research','amphora_campaign_runtime','amphora_polymer_space')
    interpreters,manifests={},{}
    for name,package in packages.items():
        forbidden=tuple(module for module in modules if module != package.replace('-','_'))
        interpreters[name]=str(install(output/name,package,forbidden))
        manifests[name]=json.loads((output/name/'manifest.json').read_bytes())
    host,port=state['endpoint'].split(':')
    env={key:value for key,value in os.environ.items() if key.upper() in {'SYSTEMROOT','WINDIR','TEMP','TMP','PATH','COMSPEC'}}
    for name in ('artifact','research'):
        url=URL.create('postgresql+psycopg',username=name+'_service',password=state['password'],host=host,port=int(port),database=state['database'])
        env['AMPHORA_'+name.upper()+'_DATABASE_URL']=url.render_as_string(hide_password=False)
        migration_env=dict(env,**{'AMPHORA_'+name.upper()+'_MIGRATION_URL':url.set(username=name+'_migrator').render_as_string(hide_password=False)})
        result=subprocess.run([interpreters[name],'-I','-m',packages[name].replace('-','_')+'.persistence.migrate'],
            env=migration_env,cwd=output,capture_output=True,text=True,encoding='utf-8',timeout=60)
        (output/(name+'-migration.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Owned migration failed; inspect migration log')
    config={**interpreters,'packages':manifests,'evidence':str(output/'http')}
    path=output/'acceptance.json';path.write_text(json.dumps(config),encoding='utf-8')
    result=subprocess.run([interpreters['controller'],'-I',str(ROOT/'services/research/tests/fitness/acceptance/probe.py'),str(path)],
        env=env,cwd=output,capture_output=True,text=True,encoding='utf-8',timeout=300)
    (output/'probe.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Fitness handoff failed; inspect '+str(output/'probe.log'))
    report=json.loads(result.stdout)
    print(json.dumps({key:report[key] for key in ('status','timestamp_local','scope','fitness','source_count','current_denial','historical_read_after_denial')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    verify(parser.parse_args().output)
