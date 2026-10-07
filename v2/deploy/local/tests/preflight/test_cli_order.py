"""Actual isolated CLI subprocess and non-executing between-campaign order."""

import json
import os
import subprocess
import sys

import pytest

from amphora_deployment import ProfileError
from amphora_deployment.replacement import CampaignCut


def command(*args):
    env = {key:value for key,value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC"}}
    env["PYTHONUTF8"] = "1"
    return subprocess.run([sys.executable, "-I", "-m", "amphora_deployment", *map(str,args)], env=env, capture_output=True, timeout=15)


def test_each_live_boundary_blocks_replacement():
    result = CampaignCut(False, 1, 1, 1).plan()
    assert result["blockers"] == ["pause_admission_first", "wait_for_campaign_terminal", "wait_for_attempt_drain", "wait_for_retention_confirmation"]
    assert result["start_order"] == result["stop_order"] == []
    with pytest.raises(ProfileError, match="cut_count"):
        CampaignCut(True, True, 0, 0).plan()
    with pytest.raises(ProfileError, match="cut_paused_shape"):
        CampaignCut(1, 0, 0, 0).plan()


def test_completed_cut_orders_restart_but_does_not_execute():
    result = CampaignCut(True, 0, 0, 0).plan()
    assert result["status"] == "order_available" and result["executes_actions"] is False
    assert result["start_order"][0] == "verify_storage_and_owner_schema_versions"
    assert result["start_order"][-1] == "enable_admission_last"
    assert result["stop_order"].index("drain_owner_deliveries_and_projections") < result["stop_order"].index("stop_owner_apis")


def test_cli_validates_and_returns_blocked_observations_without_credentials(record, tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(record))
    valid = command("validate", "--profile", path)
    assert valid.returncode == 0 and json.loads(valid.stdout)["readiness_assessed"] is False
    observed = command("preflight", "--profile", path)
    assert observed.returncode == 3
    body = json.loads(observed.stdout)
    assert "missing_environment:DEMO_AUTH" in body["blockers"] and "storage_policy_unverified" in body["blockers"]
    assert body["authorizes_installation"] is False


def test_cli_malformed_and_oversize_files_are_safe(tmp_path):
    path = tmp_path / "private-profile.json"
    for payload in (b"private-secret-input", b"x" * 65537):
        path.write_bytes(payload)
        result = command("validate", "--profile", path)
        assert result.returncode == 2 and b"private-secret-input" not in result.stdout + result.stderr
    missing = command("validate", "--profile", tmp_path / "missing-secret-path")
    assert missing.returncode == 2 and b"missing-secret-path" not in missing.stdout


def test_cli_order_has_explicit_nonexecuting_authority():
    result = command("replacement-order", "--admissions-paused", "--active-campaigns", "0", "--inflight-attempts", "0", "--pending-retentions", "0")
    assert result.returncode == 0
    body = json.loads(result.stdout)
    assert body["status"] == "order_available" and body["executes_actions"] is False
