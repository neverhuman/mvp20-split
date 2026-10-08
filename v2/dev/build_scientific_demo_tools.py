"""Qualify two independent bounded scientific tools; no campaign or science acceptance."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from build_numeric_images import ImageBuild
from install_owner_peer import install
from check_boundaries import ROOT

PACKAGES=('hansen_solvency','arrhenius_viscosity')

def build_tools(output,base):
    if not base.startswith('python@sha256:') or len(base.split(':')[-1])!=64:
        raise ValueError('digest_pinned_base_required')
    build=ImageBuild(output)
    result={'status':'building','tools':{},'base':base,'provider_calls':0}
    uv=ROOT/'.venv/Scripts/uv.exe'
    for folder in PACKAGES:
        package='amphora-'+folder.replace('_','-');module='amphora_'+folder
        project=ROOT/'tools'/folder;target=output/folder;target.mkdir()
        python=install(target/'installed',package,('amphora_campaign_runtime','amphora_agent_planning','amphora_data_artifacts','sqlalchemy'))
        shutil.copytree(project/'tests',target/'tests',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        build.run([uv,'pip','install','--python',python,'pytest>=8,<9'])
        args=[str(target/'tests'),'--confcutdir='+str(target),'--import-mode=importlib','-q','--tb=short']
        build.run([python,'-I','-c','import pytest;raise SystemExit(pytest.main('+repr(args)+'))'])
        context=target/'image';context.mkdir();local=context/'local';local.mkdir()
        for wheel in (target/'installed/wheels').glob('*.whl'):shutil.copyfile(wheel,local/wheel.name)
        build.run([uv,'export','--project',project,'--locked','--no-dev','--no-emit-local','--output-file',context/'requirements.txt'])
        (context/'Download.Dockerfile').write_text(f'FROM {base}\nCOPY requirements.txt /requirements.txt\nRUN python -m pip download --require-hashes --only-binary=:all: --dest /resolved -r /requirements.txt\nCOPY local /resolved\n')
        tag='amphora/'+folder.replace('_','-')+':ui01-'+output.name.lower()
        build.run(['docker','buildx','build','--platform','linux/amd64','--load','--provenance=false','-f',context/'Download.Dockerfile','-t',tag+'-dependencies',context])
        container=build.run(['docker','create',tag+'-dependencies']).decode().strip()
        try:build.run(['docker','cp',container+':/resolved',context/'wheels'])
        finally:build.run(['docker','rm',container])
        shutil.copyfile(project/'Dockerfile',context/'Dockerfile')
        metadata=context/'metadata.json'
        build.run(['docker','buildx','build','--platform','linux/amd64','--load','--provenance=false','--build-arg','PYTHON_BASE='+base,'--metadata-file',metadata,'-t',tag,context])
        digest=json.loads(metadata.read_bytes())['containerimage.digest']
        inspected=json.loads(build.run(['docker','image','inspect',tag]))[0]
        assert inspected['Architecture']=='amd64' and inspected['Os']=='linux' and inspected['Config']['User']=='65532:65532'
        assert digest==inspected.get('Descriptor',{}).get('digest') or any(x.endswith('@'+digest) for x in inspected.get('RepoDigests',[]))
        run=['docker','run','--rm','-i','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',digest]
        descriptor=json.loads(build.run([*run,'describe','--image-sha256',digest[7:]]))
        (target/'descriptor.json').write_text(json.dumps(descriptor,indent=2)+'\n')
        for kind in ('input','output'):
            raw=build.run([*run,'schema','--kind',kind]);assert raw==build.run([python,'-I','-m',module,'schema','--kind',kind])
            port=descriptor['tool']['inputs' if kind=='input' else 'outputs'][0]
            assert hashlib.sha256(raw).hexdigest()==port['schema_ref']['sha256']
            (target/(kind+'.json')).write_bytes(raw)
        common={'candidate_id':'fixture-polymer-A','parameter_context':'Declared synthetic parameters; not a measured novel structure.'}
        parameters={**common,**({'polymer':{'dispersion':18.,'polar':8.,'hydrogen_bond':6.},'solvent':{'dispersion':17.,'polar':6.,'hydrogen_bond':4.},'interaction_radius':4.}
            if folder=='hansen_solvency' else {'reference_viscosity_pa_s':2.,'reference_temperature_c':25.,'temperature_c':50.,'activation_energy_j_mol':20000.})}
        payload=json.dumps(parameters).encode();observed=build.run([*run,'compute'],payload)
        assert json.loads(observed)==json.loads(build.run([python,'-I','-m',module,'compute'],payload))
        (target/'parameters.json').write_bytes(payload);(target/'observation.json').write_bytes(observed)
        result['tools'][folder]={'image':digest,'module':module,'package':package,'directory':str(target),'python':str(python),'authority':'unvalidated_screen'}
        print(folder+': isolated tests and Linux calculation passed',flush=True)
    result['status']='passed';(output/'evidence.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--base',required=True)
    args=parser.parse_args();build_tools(args.output.absolute(),args.base)
