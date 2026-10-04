"""Installed HTTP restart preserves revision-pinned projection pages with peers offline."""

import json
import os
import subprocess
import sys
import urllib.error
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_contracts_knowledge import RetractAssertion

from ..acceptance.processes import Owner
from ..persistence.test_ledger import observation

pytestmark = pytest.mark.postgres


def test_installed_owner_pages_survive_replacement_new_head_and_grant_change(
    stored_graph, tmp_path
):
    case = stored_graph
    first = case.ledger.accept(
        case.principal, case.proposal, observation(case.proposal)
    )
    revision = first.decision.head.snapshot
    snapshot = case.ledger.snapshot(case.principal, revision)
    config = {
        "database_url_env": "EXPLORE_DATABASE",
        "principals": [
            {
                "token_env": "EXPLORE_TOKEN",
                "actor_id": "explorer",
                "scope": case.principal.scope.model_dump(),
                "actions": ["read_graph"],
            }
        ],
        "vocabulary": case.vocabulary.record.model_dump(mode="json"),
        "policy": case.policy.definition(),
        "data": {"endpoint": "http://127.0.0.1:1", "token_env": "EXPLORE_TOKEN"},
        "research": {"endpoint": "http://127.0.0.1:1", "token_env": "EXPLORE_TOKEN"},
    }
    path = tmp_path / "knowledge.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper()
        in {
            "SYSTEMROOT",
            "WINDIR",
            "PATH",
            "TEMP",
            "TMP",
            "COMSPEC",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
        }
    }
    environment.update(
        EXPLORE_DATABASE=case.engine.url.render_as_string(hide_password=False),
        EXPLORE_TOKEN="e" * 32,
        PYTHONUTF8="1",
    )
    python = os.environ.get("AMPHORA_TEST_KNOWLEDGE_EXPLORE_PYTHON", sys.executable)
    isolation = subprocess.run(
        [
            python,
            "-I",
            "-c",
            "import importlib.util; assert all(importlib.util.find_spec(m) is None for m in ('amphora_data_artifacts','amphora_research','amphora_campaign_runtime'))",
        ],
        env=environment,
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert isolation.returncode == 0, (
        "Select an independently installed Knowledge interpreter"
    )
    entity = snapshot.content.entities[0].reference.model_dump(mode="json")
    search = {
        "wire_version": "1",
        "revision": revision.model_dump(mode="json"),
        "limit": 1,
    }
    neighborhood = {
        "wire_version": "1",
        "revision": search["revision"],
        "focus": entity,
    }
    detail = {
        "wire_version": "1",
        "revision": search["revision"],
        "selection": {
            "kind": "assertion",
            "reference": snapshot.content.assertions[0].reference.model_dump(
                mode="json"
            ),
        },
    }
    host = Owner("amphora_knowledge", path, environment, "e" * 32, python=python)
    try:
        first_page = host.request("/v1/graph-explore/entities", search)
        continuation = {**search, "position": first_page["next_position"]}
        second_page = host.request("/v1/graph-explore/entities", continuation)
        old_neighborhood = host.request("/v1/graph-explore/neighborhood", neighborhood)
        old_detail = host.request("/v1/graph-explore/object", detail)
        catalog = host.request("/v1/graph-explore/catalog", search["revision"])
    finally:
        host.stop()
    correction = case.proposal.model_copy(
        update={
            "change_id": "retire",
            "base": first.decision.head,
            "operations": (
                RetractAssertion(
                    operation="retract_assertion",
                    assertion=snapshot.content.assertions[0].reference,
                ),
            ),
        }
    )
    next_head = case.ledger.accept(
        case.principal, correction, observation(correction)
    ).decision.head
    replacement = Owner("amphora_knowledge", path, environment, "e" * 32, python=python)
    try:
        assert replacement.request("/v1/graph-explore/entities", search) == first_page
        assert (
            replacement.request("/v1/graph-explore/entities", continuation)
            == second_page
        )
        assert (
            replacement.request("/v1/graph-explore/neighborhood", neighborhood)
            == old_neighborhood
        )
        assert replacement.request("/v1/graph-explore/object", detail) == old_detail
        assert (
            replacement.request("/v1/graph-explore/catalog", search["revision"])
            == catalog
        )
        latest = replacement.request(
            "/v1/graph-explore/neighborhood",
            {**neighborhood, "revision": next_head.snapshot.model_dump(mode="json")},
        )
        assert latest["assertions"] == [] and len(old_neighborhood["assertions"]) == 1
        assert old_detail["detail"]["retracted"] is False
        with pytest.raises(urllib.error.HTTPError) as caught:
            replacement.request(
                "/v1/graph-explore/entities",
                {
                    **continuation,
                    "revision": next_head.snapshot.model_dump(mode="json"),
                },
            )
        assert caught.value.code == 409
        caught.value.close()
    finally:
        replacement.stop()
    config["principals"][0]["actions"] = ["propose_graph"]
    path.write_text(json.dumps(config), encoding="utf-8")
    denied = Owner("amphora_knowledge", path, environment, "e" * 32, python=python)
    try:
        with pytest.raises(urllib.error.HTTPError) as caught:
            denied.request("/v1/graph-explore/entities", continuation)
        assert caught.value.code == 403
        caught.value.close()
    finally:
        denied.stop()
    output = Path(
        os.environ.get("AMPHORA_EXPLORE_EVIDENCE", str(tmp_path / "evidence.json"))
    )
    output.write_text(
        json.dumps(
            {
                "timestamp_local": datetime.now(ZoneInfo("America/Chicago")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "original": revision.model_dump(mode="json"),
                "successor": next_head.snapshot.model_dump(mode="json"),
                "first_page": first_page,
                "second_page": second_page,
                "catalog": catalog,
                "assertions_original": len(old_neighborhood["assertions"]),
                "assertions_successor": len(latest["assertions"]),
                "replacement_equality": True,
                "revoked_grant_status": 403,
                "scope": "Actual PostgreSQL, independently installed Knowledge HTTP and process replacement; synthetic accepted-input seeding, Data/Research offline; no scientific authority",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
