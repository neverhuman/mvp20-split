from types import SimpleNamespace

import pytest

from amphora_deployment.persistence.state import LABEL
from amphora_deployment.persistence.stores import ensure_store
from amphora_deployment.profile import ProfileError


@pytest.mark.parametrize('port',['','59999'])
def test_dynamic_or_changed_docker_binding_requires_explicit_repair(port):
    state=SimpleNamespace(identity='owned',record={'store_ports':{'postgres':60687}},name=lambda kind:kind)
    info={'Config':{'Image':'pinned-image','Labels':{LABEL:'owned'}},
          'Mounts':[{'Name':'postgres-data','Destination':'/data'}],
          'HostConfig':{'PortBindings':{'5432/tcp':[{'HostIp':'127.0.0.1','HostPort':port}]}}}
    class Docker:
        def inspect(self,kind,name): return {'Labels':{LABEL:'owned'}} if kind=='volume' else info
        def run(self,*args,**kwargs): raise AssertionError('No implicit restart or replacement allowed')
    with pytest.raises(ProfileError,match='fixed_port_repair_required'):
        ensure_store(Docker(),state,'postgres','pinned-image',5432,'/data',{})


def test_stable_binding_preserves_existing_routing_without_restart():
    state=SimpleNamespace(identity='owned',record={'store_ports':{'postgres':60687}},name=lambda kind:kind)
    ports={'5432/tcp':[{'HostIp':'127.0.0.1','HostPort':'60687'}]}
    info={'Config':{'Image':'pinned-image','Labels':{LABEL:'owned'}},
          'Mounts':[{'Name':'postgres-data','Destination':'/data'}],
          'HostConfig':{'PortBindings':ports},'NetworkSettings':{'Ports':ports},'State':{'Running':True}}
    class Docker:
        def inspect(self,kind,name): return {'Labels':{LABEL:'owned'}} if kind=='volume' else info
        def run(self,*args,**kwargs): raise AssertionError('Healthy retained container must not restart')
    result=ensure_store(Docker(),state,'postgres','pinned-image',5432,'/data',{})
    assert result['port']==60687 and result['volume']=='postgres-data'
