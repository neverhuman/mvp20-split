"""Configured route failures distinguish durable success from unavailable work."""
import asyncio

import httpx
import pytest
from amphora_research.scientific_api.store import ScientificInputStore
from amphora_research.transport.host import ResearchHost
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from .test_routes import configuration, secrets
from .test_store import prepared

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("after_commit",[False,True])
def test_owner_failure_before_or_after_commit_preserves_truthful_retry(ledger,monkeypatch,after_commit):
    store,resolved,_ = prepared(ledger)
    bound = resolved.bound
    secrets(monkeypatch,store.engine)
    config = configuration(bound.configured.scope,["assess_eligibility","read_scientific_assessment"])
    config["science"]["eligibility_profiles"] = [bound.configured.document.model_dump(mode="json")]
    monkeypatch.setattr("amphora_research.scientific_api.workflow.ScientificInputResolver.resolve",lambda *args:resolved)
    complete = ScientificInputStore.complete
    calls = []
    def fail(self, *args):
        calls.append("complete")
        if after_commit:
            complete(self,*args)
        raise SQLAlchemyError("injected_owner_failure")
    host = ResearchHost.configured(config)
    try:
        with TestClient(host.app) as client:
            headers = {"Authorization":"Bearer "+"s"*32}
            query = bound.request.model_dump(mode="json")
            with monkeypatch.context() as patch:
                patch.setattr(ScientificInputStore,"complete",fail)
                response = client.post("/v1/scientific-assessments",headers=headers,json=query)
            assert response.status_code == 503 and response.json() == {"code":"scientific_owner_unavailable"}
            assert response.headers["cache-control"] == "no-store"
            before = client.post("/v1/scientific-assessments/read",headers=headers,json=query)
            assert before.status_code == 200
            assert before.json()["outcome"]["status"] == ("assessed" if after_commit else "pending")
            recovered = client.post("/v1/scientific-assessments",headers=headers,json=query)
            assert recovered.status_code == 200 and recovered.json()["outcome"]["status"] == "assessed"
            if after_commit:
                assert recovered.content == before.content
            assert client.post("/v1/scientific-assessments",headers=headers,json=query).content == recovered.content
            assert calls == ["complete"]
    finally:
        host.close()


def test_incomplete_stream_hits_real_body_deadline_without_accepting_intent(ledger,monkeypatch):
    store,resolved,_ = prepared(ledger)
    bound = resolved.bound
    secrets(monkeypatch,store.engine)
    host = ResearchHost.configured(configuration(bound.configured.scope,["assess_eligibility","read_scientific_assessment"]))
    cancelled = []
    async def body():
        yield b'{"wire_version":"1",'
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.append(True)
        yield b'"incomplete":true}'
    async def invoke():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=host.app),base_url="http://fixture") as client:
            return await client.post("/v1/scientific-assessments",headers={"Authorization":"Bearer "+"s"*32,
                "Content-Type":"application/json"},content=body())
    try:
        response = asyncio.run(invoke())
        assert response.status_code == 408 and response.json() == {"code":"request_timeout"}
        assert response.headers["cache-control"] == "no-store" and cancelled == [True]
        assert store.read(bound.configured.scope,bound.actor,"eligibility",bound.request.decision_id) is None
    finally:
        host.close()
