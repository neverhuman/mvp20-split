"""Actual independently installed read-only Research HTTP and retained-state replacement."""

import json
import os
import subprocess
import sys
import urllib.error
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_contracts_research import MissingMeasurement

from ..assessment.live_peers import Owner
from ..scientific_api.test_routes import configuration
from .test_api import queries

pytestmark = pytest.mark.postgres


def test_installed_views_survive_replacement_and_future_only_correction(
    prepared, tmp_path
):
    case = prepared
    config = configuration(case.scope, ["read_scientific_record"])
    path = tmp_path / "research.json"
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
        SCIENCE_DB=case.engine.url.render_as_string(hide_password=False),
        SCIENCE_TOKEN="s" * 32,
        SCIENCE_READ_TOKEN="r" * 32,
        SCIENCE_PUBLISH_TOKEN="p" * 32,
        PYTHONUTF8="1",
    )
    python = os.environ.get("AMPHORA_TEST_RESEARCH_EXPLORE_PYTHON", sys.executable)
    isolation = subprocess.run(
        [
            python,
            "-I",
            "-c",
            "import importlib.util; assert all(importlib.util.find_spec(m) is None for m in ('amphora_data_artifacts','amphora_knowledge','amphora_campaign_runtime'))",
        ],
        env=environment,
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert isolation.returncode == 0, "Select independently installed Research"
    query = queries(case)
    host = Owner("amphora_research", path, environment, "s" * 32, python)
    try:
        original = {
            name: host.request("/v1/research-explore/" + name, value)
            for name, value in query.items()
        }
        continuation = {
            **query["properties"],
            "position": original["properties"]["next_position"],
        }
        second = host.request("/v1/research-explore/properties", continuation)
        series_continuation = {
            **query["observation-series"],
            "position": original["observation-series"]["next_position"],
        }
        series_second = host.request(
            "/v1/research-explore/observation-series", series_continuation
        )
    finally:
        host.stop()
    corrected = case.first.model_copy(
        update={
            "reference": case.first.reference.model_copy(update={"revision": 2}),
            "supersedes": case.first.reference,
            "value": MissingMeasurement(kind="missing", reason="report_corrected"),
        }
    )
    case.store.publish(case.scope, "fixture", corrected)
    successor = {
        **query["properties"],
        "observations": [
            corrected.reference.model_dump(mode="json"),
            query["properties"]["observations"][1],
        ],
    }
    replacement = Owner("amphora_research", path, environment, "s" * 32, python)
    try:
        for name, value in query.items():
            assert (
                replacement.request("/v1/research-explore/" + name, value)
                == original[name]
            )
        assert (
            replacement.request("/v1/research-explore/properties", continuation)
            == second
        )
        assert (
            replacement.request(
                "/v1/research-explore/observation-series", series_continuation
            )
            == series_second
        )
        newer = replacement.request("/v1/research-explore/properties", successor)
        assert newer["rows"][0]["value"]["kind"] == "missing"
        assert original["properties"]["rows"][0]["value"]["kind"] == "numeric"
        with pytest.raises(urllib.error.HTTPError) as caught:
            replacement.request(
                "/v1/research-explore/properties",
                {**successor, "position": original["properties"]["next_position"]},
            )
        assert caught.value.code == 409
        caught.value.close()
    finally:
        replacement.stop()
    config["principals"][0]["actions"] = ["read_scientific_impact"]
    path.write_text(json.dumps(config), encoding="utf-8")
    denied = Owner("amphora_research", path, environment, "s" * 32, python)
    try:
        with pytest.raises(urllib.error.HTTPError) as caught:
            denied.request("/v1/research-explore/properties", continuation)
        assert caught.value.code == 403
        caught.value.close()
    finally:
        denied.stop()
    output = Path(
        os.environ.get(
            "AMPHORA_RESEARCH_EXPLORE_EVIDENCE", str(tmp_path / "evidence.json")
        )
    )
    output.write_text(
        json.dumps(
            {
                "timestamp_local": datetime.now(ZoneInfo("America/Chicago")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "experiment": query["catalog"],
                "original_query": query["properties"],
                "successor_query": successor,
                "original_value": original["properties"]["rows"][0]["value"],
                "successor_value": newer["rows"][0]["value"],
                "series_first": original["observation-series"]["points"],
                "series_second": series_second["points"],
                "replacement_equality": True,
                "grant_removed_status": 403,
                "scope": "Actual PostgreSQL and independently installed Research HTTP/replacement; synthetic owner-local seeding, Data offline, no scientific validation",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
