from pathlib import Path
from types import SimpleNamespace

from amphora_deployment.lifecycle.health import observe, observe_owner


def test_static_health_does_not_mask_database_check_failure(monkeypatch):
    class Response:
        status=200
        def read(self, limit): return b'{"status":"ok"}'
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr('urllib.request.build_opener',lambda *args:SimpleNamespace(open=lambda *a,**k:Response()))
    calls=[]
    def run(command,**kwargs):
        calls.append((command,kwargs))
        return SimpleNamespace(returncode=2)
    monkeypatch.setattr('subprocess.run',run)
    binding=SimpleNamespace(port=18080,directory=Path('installed'),configuration=Path('config.json'),
                            environment={'AMPHORA_RUNTIME_DATABASE_URL':'private-value'})
    report=observe_owner('runtime',binding)
    assert report=={'http':'available','database':'unavailable'}
    assert calls[0][0][3:]==['amphora_campaign_runtime','check','--config','config.json']
    assert 'private-value' not in str(report) and 'private-value' not in str(calls[0][0])


def test_gateway_cannot_confer_peer_readiness(monkeypatch):
    monkeypatch.setattr('amphora_deployment.lifecycle.health.observe_owner',lambda owner,binding:
        {'http':'available','database':'not_applicable' if owner=='gateway' else 'unavailable'})
    report=observe({'gateway':None,'runtime':None})
    assert report['infrastructure']=='unavailable'
    assert report['scientific_eligibility']=='not_assessed'
