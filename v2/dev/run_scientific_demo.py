"""Run actual scientific workers in a separate retained campaign; zero provider calls."""
import argparse
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from amphora_deployment.credentials import CredentialVault
from amphora_deployment.lifecycle.routes import Routes
from amphora_deployment.persistence.state import LocalState
from local_demo_controller import Controller
from local_numeric_configuration import prepare,write
from scientific_execution.materials import prepare_materials
from scientific_execution.configuration import bind
from scientific_execution.campaign import ScientificCampaign

def run(args):
    root=args.root.absolute();output=args.output.absolute();original=LocalState.snapshot(root);routes=Routes.load(root)
    source=json.loads(args.source_manifest.read_bytes())['owners']
    registry_python=Path(source['registry']['installation'])/'environment/Scripts/python.exe'
    knowledge_records=json.loads((args.knowledge_records/'records.json').read_bytes()) if args.knowledge_records else None
    scope=knowledge_records['scope'] if knowledge_records else {'tenant_id':'internal','project_id':'scientific-demo-'+uuid.uuid4().hex}
    prepare_materials(args.tools.absolute(),output.parent/(output.name+'-materials'),scope,registry_python,knowledge_records['knowledge'] if knowledge_records else None)
    material,identity,ports=prepare(output,args.bundle.absolute(),output.parent/(output.name+'-materials'),args.source_manifest.absolute(),original['deployment_id'],routes,delivery=True)
    if knowledge_records:
        from scientific_execution.knowledge_configuration import connect
        connect(output,args.knowledge_records)
    bind(output,args.bundle.absolute(),material,identity,ports,'awaiting-admission','standby')
    runtime_python=Path(source['runtime']['installation'])/'environment/Scripts/python.exe'
    secrets=CredentialVault(root/'credentials.dpapi',original['deployment_id']).load().environment(['REGISTRY_OPERATOR_TOKEN','RUNTIME_OPERATOR_TOKEN','ARTIFACT_OPERATOR_TOKEN','RUNTIME_ARTIFACT_TOKEN'])
    campaign=ScientificCampaign(None,output,material,secrets,runtime_python)
    if args.prepare_only:
        write(output/'prepared.json',{'scope':scope,'bundle':str(args.bundle.absolute()),'ports':ports,'material':material,'identity':str(identity.directory)})
        print('Scientific graph compiled; owners and workers not started',flush=True);return
    controller=None
    try:
        controller=Controller(root,output,routes,'standby');campaign.controller=controller;controller.start_owners(secrets['REGISTRY_OPERATOR_TOKEN'])
        def registry(action,payload):
            result=campaign.call('registry','/v1/registry/'+action,campaign.identity('registry.'+action,payload));assert result['status']=='accepted',result['reason_code'];return result
        for stage,lock in material['locks'].items():
            registry('register',{'scope':scope,'descriptor':campaign.releases[stage],'expected_lock':lock})
            registry('activate',{'release':lock,'expected_revision':1})
            registry('deploy',{'deployment_id':stage,'release':lock,'architecture':'x86_64','operating_system':'linux','workers':['science-slot']})
        run_id=campaign.admit();write(output/'admission.json',{'scope':scope,'run_id':run_id,'receipt':campaign.admission,'command':campaign.admission_command})
        controller.drain();controller.close();controller=None
        bind(output,args.bundle.absolute(),material,identity,ports,run_id,'admitted')
        controller=Controller(root,output,routes,'admitted');campaign.controller=controller;controller.start_owners(secrets['REGISTRY_OPERATOR_TOKEN'])
        for name in controller.control('/status')['scientific_workers']:controller.control('/scientific-workers/'+name+'/standby','POST')
        controller.wait(lambda:all(row['state']=='observed' and row['observation']['free_slots']==1 for row in controller.control('/status')['tool_catalog'].values()))
        for name in ('runtime-deliver','runtime-coordinate'):controller.control('/workers/'+name+'/start','POST')
        for name in controller.control('/status')['scientific_workers']:controller.control('/scientific-workers/'+name+'/start','POST')
        deadline=time.monotonic()+600;previous=None
        while True:
            graph=campaign.graph();status=controller.control('/status');write(output/'latest-observation.json',{'graph':graph,'controller':status})
            state=(graph['status'],graph['spent'])
            if state!=previous:print('Scientific campaign: '+str(state),flush=True);previous=state
            if graph['status']!='running':break
            assert time.monotonic()<deadline,'Scientific campaign exceeded600seconds'
            assert not any(x['faulted'] for x in status['workers'].values()),'Native worker fault'
            assert not any(x['faulted'] for x in status['scientific_workers'].values()),'Scientific worker fault'
            time.sleep(1)
        for name in status['scientific_workers']:controller.control('/scientific-workers/'+name+'/quiesce','POST')
        controller.wait(lambda:all(not x['active_turn'] for x in controller.control('/status')['scientific_workers'].values()))
        result=campaign.evidence();final=controller.drain();controller.close();controller=None
        assert LocalState.snapshot(root)==original
        write(output/'evidence.json',{'status':'passed','scope':scope,'run_id':run_id,'result':result,'final':final,'provider_calls':0,
            'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'limits':['Four actual scientific calculations over synthetic parameters; not validated predictions or generated structures.','Graph curated by Codex, not runtime LLM output.']})
        print('Four scientific invocations retained; owners drained',flush=True)
    except BaseException as error:
        failure={'status':'failed','error_type':type(error).__name__,'run_id':campaign.run_id,'provider_calls':0}
        if controller is not None:
            try:
                failure['cancellation']=campaign.cancel_after_failure();failure['drain']=controller.drain()
            finally:controller.close()
        write(output/'failure.json',failure)
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('root','output','bundle','tools','source-manifest'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--knowledge-records',type=Path)
    parser.add_argument('--prepare-only',action='store_true');run(parser.parse_args())
