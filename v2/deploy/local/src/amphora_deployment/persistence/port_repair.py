"""Explicit forward repair for owned dynamic-port containers; retains data and baseline."""

from datetime import datetime

from ..credentials import CredentialVault
from ..profile import require
from .docker import Docker
from .migrations import require_stopped
from .state import LocalState
from .stores import POSTGRES, QDRANT, ensure_store, owned


def repair(root, kind):
    require(kind in ('postgres','qdrant'), 'deployment_store_kind')
    with LocalState(root) as state:
        require(state.record.get('phase')=='stores_ready','deployment_stores_required')
        require_stopped(state.record.get('routes'))
        before=dict(state.record[kind])
        image,port,mount=(POSTGRES,5432,'/var/lib/postgresql/data') if kind=='postgres' else (QDRANT,6333,'/qdrant/storage')
        require(before['container']==state.name(kind) and before['volume']==state.name(kind+'-data') and
                before['image']==image and before['host']=='127.0.0.1','deployment_repair_identity')
        docker=Docker()
        info=docker.inspect('container',before['container'])
        owned(info,state.identity,container=True)
        owned(docker.inspect('volume',before['volume']),state.identity)
        require(info['Config']['Image']==image and len(info['Mounts'])==1 and
                info['Mounts'][0].get('Name')==before['volume'] and info['Mounts'][0].get('Destination')==mount,
                'deployment_repair_mount')
        bindings=info['HostConfig']['PortBindings']
        require(bindings=={str(port)+'/tcp':[{'HostIp':'127.0.0.1','HostPort':''}]},'deployment_repair_requires_dynamic_port')
        archive=before['container']+'-dynamic-baseline'
        require(docker.inspect('container',archive) is None,'deployment_repair_baseline_exists')
        bundle=CredentialVault(state.root/'credentials.dpapi',state.identity).load()
        environment=({'POSTGRES_PASSWORD':bundle.environment(['PG_ADMIN_PASSWORD'])['PG_ADMIN_PASSWORD'],'POSTGRES_DB':'amphora_local'}
                     if kind=='postgres' else {'QDRANT__SERVICE__API_KEY':bundle.environment(['QDRANT_API_KEY'])['QDRANT_API_KEY']})
        record={'status':'started','at':datetime.now().astimezone().isoformat(timespec='seconds'),
                'baseline_container':archive,'retained_volume':before['volume'],'port':before['port']}
        state.record.setdefault('port_repairs',{})[kind]=record
        state.record.setdefault('store_ports',{})[kind]=before['port']
        state.save()
        try:
            docker.run('stop','--time','10',before['container'])
            docker.run('rename',before['container'],archive)
            after=ensure_store(docker,state,kind,image,port,mount,environment)
            require(after==before,'deployment_repair_identity_changed')
            record['status']='completed'
        except Exception:
            record['status']='failed_forward_repair_required'
            state.save()
            raise
        state.save()
        return dict(record)
