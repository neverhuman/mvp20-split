"""Installed public registration survives process death with exact retry identity."""
import http.client
import json
import os
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ..assessment.live_peers import Owner
from .test_registration import metadata


@pytest.mark.parametrize("stage", ["before_commit", "after_commit"])
def test_installed_registration_process_death_and_replacement(registration, tmp_path, stage):
    initial = os.environ.get("AMPHORA_TEST_DECLARATION_PYTHON")
    replacement = os.environ.get("AMPHORA_TEST_DECLARATION_REPLACEMENT_PYTHON")
    if not initial or not replacement:
        pytest.skip("Explicit independently installed registration environments required")
    registrar, principal, question, need = registration
    config = {"database_url_env": "DECLARATION_DB", "declarations": True,
        "principals": [{"token_env": "DECLARATION_TOKEN", "actor_id": principal.actor_id,
            "scope": principal.scope.model_dump(), "actions": ["declare_question", "declare_evidence_need", "read_declarations"]}]}
    path = tmp_path / "research.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA"}}
    environment.update(DECLARATION_DB=registrar.ledger.engine.url.render_as_string(hide_password=False),
        DECLARATION_TOKEN="d" * 32, PYTHONUTF8="1")
    body = question.model_dump(mode="json")
    host = Owner("amphora_research", path, environment, "d" * 32, initial, barrier=stage,
        fault_host=Path(__file__).with_name("fault_host.py"))
    before = None
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(host.request, "/v1/questions", body)
        try:
            assert host.events.get(timeout=15) == {"barrier": stage}
            before = metadata(registrar, question)
            assert (before is not None) == (stage == "after_commit")
        finally:
            host.stop()
        with pytest.raises((OSError, ConnectionError, http.client.HTTPException)):
            future.result(timeout=10)
    config["principals"][0]["actor_id"] = "replacement-registrant"
    path.write_text(json.dumps(config), encoding="utf-8")
    host = Owner("amphora_research", path, environment, "d" * 32, replacement)
    try:
        assert host.request("/v1/questions", body) == body
        assert host.request("/v1/questions/read", body["reference"]) == body
        assert host.request("/v1/evidence-needs", need.model_dump(mode="json")) == need.model_dump(mode="json")
        with pytest.raises(urllib.error.HTTPError) as conflict:
            host.request("/v1/questions", body | {"objective": "altered retry"})
        assert conflict.value.code == 409
        after = metadata(registrar, question)
        if stage == "after_commit":
            assert after == before
        else:
            assert after.actor_id == "replacement-registrant" and not after.preexisting
    finally:
        host.stop()
