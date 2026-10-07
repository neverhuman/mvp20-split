import io
from types import SimpleNamespace

from amphora_deployment.lifecycle.processes import OwnerProcess


class Events:
    def __init__(self): self.records=[]
    def emit(self, owner, event, **metadata): self.records.append(event)


def test_drain_is_once_only_and_timeout_does_not_terminate(monkeypatch):
    clock=[100.0]
    monkeypatch.setattr('amphora_deployment.lifecycle.processes.time.monotonic',lambda:clock[0])
    process=SimpleNamespace(pid=42,stdin=io.BytesIO(),poll=lambda:None)
    # No terminate/kill/wait methods: timeout must only report state.
    events=Events()
    owner=OwnerProcess('runtime',process,None,events)
    assert owner.drain()['drain']=='draining'
    clock[0]+=46
    assert owner.drain()['drain']=='timed_out'
    assert process.stdin.getvalue()==b'D'
    assert events.records==['draining']


def test_drain_reports_actual_exit_and_emits_success_only_once():
    code=[None]
    events=Events()
    process=SimpleNamespace(pid=42,stdin=io.BytesIO(),poll=lambda:code[0])
    owner=OwnerProcess('runtime',process,None,events)
    owner.drain()
    code[0]=0
    assert owner.status()['drain']=='drained'
    assert owner.status()['drain']=='drained'
    assert events.records==['draining','drained']
    code[0]=2
    assert owner.status()['drain']=='failed'
