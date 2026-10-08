"""Actual-owner commands and readback for the scientific fixture; no peer SQL."""
import hashlib
import json
import os
import subprocess
import urllib.parse
from check_boundaries import ROOT
from local_numeric_campaign import Campaign
from local_numeric_configuration import write
from .definition import CAMPAIGN_ID

class ScientificCampaign(Campaign):
    def __init__(self,controller,output,material,tokens,runtime_python):
        self.controller,self.output,self.material,self.tokens=controller,output,material,tokens
        self.scope,self.run_id=material['scope'],None
        self.releases={stage:json.loads((output/(stage+'-descriptor.json')).read_bytes()) for stage in material['locks']}
        environment={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','LOCALAPPDATA','APPDATA','COMSPEC'}}
        script=ROOT/'services/campaign_runtime/tests/scheduling/acceptance/compile_plans.py'
        result=subprocess.run([str(runtime_python),'-I',str(script),str(output/'runtime.json')],env=environment,capture_output=True,timeout=30)
        if result.returncode:
            (output/'compiler-error.txt').write_bytes(result.stderr)
            raise ValueError('Scientific graph compilation failed; see compiler-error.txt')
        self.plan=json.loads(result.stdout)[CAMPAIGN_ID]
        self.compiler_probe_sha256=hashlib.sha256(script.read_bytes()).hexdigest()
        write(output/'compiled-plan.json',self.plan)

    def admit(self):
        definition=json.loads((self.output/'graph.json').read_bytes());inputs=[]
        for port in definition['body']['inputs']:
            if port['name']=='campaign_context':
                artifact=self.publish((self.output/'campaign-context.json').read_bytes(),port['value_type']['schema_ref'])
                inputs.append({'port':port['name'],'value':{'kind':'artifact','artifact':artifact,
                    'representation':port['value_type']['representation'],'unit':port['value_type']['unit']}})
                write(self.output/'context-artifact.json',artifact)
                continue
            stage='hansen_solvency' if port['name'].endswith('hansen_solvency') else 'arrhenius_viscosity'
            parameters=json.loads((self.output/(stage+'-parameters.json')).read_bytes())
            parameters['candidate_id']='fixture-polymer-B' if port['name'].startswith('candidate_b') else 'fixture-polymer-A'
            if parameters['candidate_id'].endswith('B'):
                if stage=='hansen_solvency':parameters['polymer']['polar']=14.
                else:parameters['reference_viscosity_pa_s']=5.
            body=json.dumps(parameters,separators=(',',':')).encode()
            artifact=self.publish(body,port['value_type']['schema_ref'])
            inputs.append({'port':port['name'],'value':{'kind':'artifact','artifact':artifact,
                'representation':port['value_type']['representation'],'unit':port['value_type']['unit']}})
        self.admission_command=self.identity('graph.admit',{'plan_sha256':self.plan['sha256'],'inputs':inputs,
            'budget':{'limit':8,'max_attempts_per_activation':2}})
        self.admission_path='/v1/graph-runs'
        self.admission=self.call('runtime',self.admission_path,self.admission_command)
        assert self.admission['outcome']['status']=='accepted',self.admission['outcome']
        self.run_id=self.admission['outcome']['committed']['object_id'];return self.run_id

    def evidence(self):
        graph=self.graph();assert graph['status']=='completed' and graph['spent']==4 and graph['reserved']==0
        page=self.call('runtime','/v1/graph-observations/'+self.run_id+'/nodes?limit=100')
        assert page['next_cursor'] is None and len(page['nodes'])==5
        token=urllib.parse.quote(page['snapshot']['snapshot_token'],safe='');reports=[]
        for node in page['nodes']:
            if node['kind']!='invoke':continue
            detail=self.call('runtime','/v1/graph-observations/'+self.run_id+'/nodes/'+node['activation_id']+'?snapshot_token='+token)
            accepted=[x for x in detail['attempts'] if x['canonical_result']]
            assert len(accepted)==1 and accepted[0]['status']=='succeeded'
            completion=self.call('runtime','/v1/runs/'+self.run_id+'/completions/'+accepted[0]['completion_id'])
            artifact=completion['result']['outcome']['outputs'][0]['artifact'];result=self.artifact_bytes(artifact)
            assert result['scientific_status']=='unvalidated_screen'
            reports.append({'node':node,'completion':completion,'artifact':artifact,'result':result})
        assert len(reports)==4
        results={(r['result']['candidate_id'],r['artifact']['schema_ref']['schema_id']):r['result'] for r in reports}
        assert results[('fixture-polymer-A','materials.hansen-solvency.output')]['sphere_position']=='inside'
        assert results[('fixture-polymer-B','materials.hansen-solvency.output')]['sphere_position']=='outside'
        write(self.output/'canonical-completions.json',reports)
        reservations=[i for r in reports for i in r['completion']['retention_reservation_ids']]
        self.controller.wait(lambda:all(self.call('artifact','/v1/reservations/'+i,reference='RUNTIME_ARTIFACT_TOKEN')['outcome']['status']=='confirmed' for i in reservations),timeout=120)
        return {'graph':graph,'reports':reports,'compiler_probe_sha256':self.compiler_probe_sha256}
