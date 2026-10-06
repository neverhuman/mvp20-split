import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.openai_provider import MODEL, OpenAIPrice, OpenAIProvider
from amphora_agent_planning.openai_provider.http import MAX_ENVELOPE, OpenAIHTTP
from amphora_agent_planning.openai_provider.input import (
    PreparedInput,
    tokenizer_reference,
)
from amphora_agent_planning.providers.capture import observe
from amphora_agent_planning.providers.port import ProviderUnavailable
from amphora_contracts_core import Scope
from amphora_contracts_planning import reference_proposal_schema


def bound():
    value=json.loads((Path(__file__).parents[1]/"providers/fixtures/request.json").read_bytes())
    context=value["context"]; bodies={}
    context["output_schema"]=reference_proposal_schema().model_dump(mode="json")
    refs=[context["prompt"],context["objective"],context["policy"],context["model"]["configuration"],*(x["artifact"] for x in context["entries"])]
    for ref in refs:
        raw=("Return JSON only. Abstain if uncertain." if ref is context["prompt"] else "Synthetic engineering input.").encode()
        ref.update(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw));bodies[ref["sha256"]]=raw
    context["model"].update(provider_id="openai",model_id=MODEL,model_revision=MODEL,context_window_tokens=400000,tokenizer=tokenizer_reference().model_dump(mode="json"))
    context["limits"].update(max_input_tokens=8192,max_output_tokens=2048,max_attempts=1,total_tokens=10240,total_accounting_units=1000000000,accounting_unit="usd_nanodollars")
    scope=Scope.model_validate(value["reference"]["scope"])
    return AttemptBinding(RequestSnapshot.from_bytes(json.dumps(value).encode(),actor_id=value["actor_id"],scope=scope),1), lambda ref:bodies[ref.sha256]


def response(*,status="completed",usage=None,content=None):
    text=json.dumps({"schema_version":"1","action":"abstain","rationale":"Synthetic evidence insufficient.","payload":None})
    return json.dumps({"model":MODEL,"status":status,"usage":usage if usage is not None else {"input_tokens":100,"output_tokens":50,"output_tokens_details":{"reasoning_tokens":40}},
        "output":[{"type":"reasoning"},{"type":"message","role":"assistant","content":content if content is not None else [{"type":"output_text","text":text}]}]}).encode()


def provider(raw):
    attempt,reader=bound()
    transport=SimpleNamespace(send=lambda _:raw)
    return attempt,OpenAIProvider(transport,reader)


def test_exact_input_model_price_and_output_usage():
    attempt,reader=bound();prepared=PreparedInput.bind(attempt,reader);body=json.loads(prepared.body)
    assert prepared.request_sha256==attempt.request.sha256
    assert prepared.reservation==15360000
    assert body["model"]==MODEL and body["store"] is False and body["max_output_tokens"]==2048
    assert "tools" not in body and "previous_response_id" not in body
    a,p=provider(response());result=observe(a,p).document()
    assert result.status=="abstained"
    assert result.usage.accounting_units==300000
    assert result.usage.output_tokens==50  # includes reasoning; never add40 again


@pytest.mark.parametrize("usage",[{}, {"input_tokens":True,"output_tokens":3}, {"input_tokens":-1,"output_tokens":2}])
def test_missing_or_invalid_usage_is_unknown_not_zero(usage):
    a,p=provider(response(usage=usage));assert observe(a,p).document().usage.certainty=="unknown"


@pytest.mark.parametrize("raw",[b"{",b'{"model":1,"model":2}',b'{"model":NaN}',b"x"*(MAX_ENVELOPE+1),b"[]",b'{"model":"wrong"}'], ids=["malformed","duplicate","nonfinite","oversize","array","wrong_model"])
def test_invalid_envelope_never_becomes_success(raw):
    a,p=provider(raw);result=observe(a,p).document();assert result.status=="unknown" and result.usage.certainty=="unknown"


@pytest.mark.parametrize("status,content",[("incomplete",None),("completed",[{"type":"refusal","refusal":"no"}])])
def test_truncation_and_provider_refusal_are_not_scientific_abstention(status,content):
    a,p=provider(response(status=status,content=content));result=observe(a,p).document()
    assert result.status=="unknown" and result.usage.certainty=="reported"
    assert not result.output_complete


def test_oversize_model_text_is_bounded_and_charged():
    a,p=provider(response(content=[{"type":"output_text","text":"x"*65537}]))
    result=observe(a,p).document();assert result.status=="invalid" and result.captured_bytes==65536
    assert result.usage.accounting_units==300000


def test_selected_artifact_and_input_ceiling_are_checked_before_network():
    a,reader=bound()
    with pytest.raises(ValueError,match="openai_artifact_binding"):PreparedInput.bind(a,lambda _:b"forged")
    d=a.request.document();ctx=d.context
    lowered=ctx.model_copy(update={"limits":ctx.limits.model_copy(update={"max_input_tokens":1024})})
    small=AttemptBinding(RequestSnapshot.bind(d.model_copy(update={"context":lowered}),actor_id=d.actor_id,scope=d.reference.scope),1)
    with pytest.raises(ValueError,match="openai_input_reservation_exceeded"):PreparedInput.bind(small,reader)
    assert not OpenAIProvider(None,reader).supports(ctx.model.model_copy(update={"model_revision":"unreviewed"}))
    with pytest.raises(ValueError):OpenAIPrice().estimate(True,3)


class Connection:
    sock=None
    def __init__(self,status=200,body=b"{}"):
        self.status,self.body,self.calls,self.closed=status,body,[],False
    def request(self,*args,**kwargs):self.calls.append((args,kwargs))
    def getresponse(self):return self
    def read1(self,size):chunk,self.body=self.body[:size],self.body[size:];return chunk
    def close(self):self.closed=True


@pytest.mark.parametrize("status",[301,401,429,500])
def test_http_one_request_no_redirect_or_retry(status):
    c=Connection(status,b"secret error body")
    client=OpenAIHTTP("test-key",connection_factory=lambda host,timeout:c)
    with pytest.raises(ProviderUnavailable):client.send(b"{}")
    assert len(c.calls)==1 and c.closed
    assert client.last_failure["http_status"]==status and client.last_failure["code"]=="unclassified"
    assert c.calls[0][0][:2]==("POST","/v1/responses")


def test_http_success_limit_and_cleanup():
    c=Connection();assert OpenAIHTTP("test-key",connection_factory=lambda host,timeout:c).send(b"{}") == b"{}"
    assert c.closed
    c=Connection(body=b"x"*(MAX_ENVELOPE+1))
    with pytest.raises(ValueError,match="openai_response_limit"):OpenAIHTTP("test-key",connection_factory=lambda host,timeout:c).send(b"{}")
    assert c.closed
    with pytest.raises(ValueError):OpenAIHTTP("")
    with pytest.raises(ValueError):OpenAIHTTP("test",timeout_seconds=0)


def test_http_expired_request_and_interrupted_body_close_without_retry(monkeypatch):
    import amphora_agent_planning.openai_provider.http as module
    clock=iter([0,46]);monkeypatch.setattr(module.time,"monotonic",lambda:next(clock))
    c=Connection()
    with pytest.raises(TimeoutError):OpenAIHTTP("test-key",connection_factory=lambda host,timeout:c).send(b"{}")
    assert c.closed and len(c.calls)==1
    clock=iter([0,1,2]);monkeypatch.setattr(module.time,"monotonic",lambda:next(clock))
    class Interrupted(Connection):
        def read1(self,size):raise TimeoutError("transport interrupted")
    c=Interrupted()
    with pytest.raises(TimeoutError):OpenAIHTTP("test-key",connection_factory=lambda host,timeout:c).send(b"{}")
    assert c.closed and len(c.calls)==1


def test_error_diagnostic_is_closed_metadata_never_provider_message():
    c=Connection(429,json.dumps({'error':{'code':'insufficient_quota','message':'secret-key-value','param':'secret-key-value'}}).encode())
    client=OpenAIHTTP('test-key',connection_factory=lambda host,timeout:c)
    with pytest.raises(ProviderUnavailable):client.send(b'{}')
    assert client.last_failure['code']=='insufficient_quota'
    assert client.last_failure['parameter'] is None and 'secret' not in json.dumps(client.last_failure)
