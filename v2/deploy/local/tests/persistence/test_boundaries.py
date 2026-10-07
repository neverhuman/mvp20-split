"""Local journal serialization and rejection of foreign container ownership."""

import json
import os
import subprocess
import sys

import pytest

from amphora_deployment import ProfileError
from amphora_deployment.persistence.state import LABEL, LocalState
from amphora_deployment.persistence.stores import new_credentials, owned


@pytest.mark.skipif(os.name != "nt", reason="Windows byte-range lock")
def test_current_process_lock_and_fresh_process_exclusion(tmp_path):
    with LocalState(tmp_path) as state:
        identity = state.identity
        script = "import sys; from amphora_deployment.persistence.state import LocalState; from amphora_deployment import ProfileError\n"
        script += "try:\n with LocalState(sys.argv[1]): raise SystemExit(9)\nexcept ProfileError as e:\n assert str(e)=='deployment_operation_busy'\n"
        result = subprocess.run([sys.executable, "-I", "-c", script, str(tmp_path)], capture_output=True, timeout=15)
        assert result.returncode == 0
        state.record["phase"] = "test_checkpoint"
        state.save()
    with LocalState(tmp_path) as resumed:
        assert resumed.identity == identity and resumed.record["phase"] == "test_checkpoint"
        assert resumed.name("postgres") == "amphora-local-" + identity + "-postgres"
        with pytest.raises(ProfileError, match="deployment_resource_kind"):
            resumed.name("../other")
    assert not list(tmp_path.glob("*.tmp"))


def test_foreign_or_missing_resource_cannot_be_started():
    for info in (None, {"Labels": {}}, {"Labels": {LABEL: "someone-else"}}):
        with pytest.raises(ProfileError):
            owned(info, "ours")
    owned({"Labels": {LABEL: "ours"}}, "ours")
    owned({"Config": {"Labels": {LABEL: "ours"}}}, "ours", container=True)


def test_generated_roles_and_tokens_are_distinct_and_not_a_shared_admin():
    bundle = new_credentials()
    values = bundle.environment(bundle.names)
    assert len(values) == len(set(values.values()))
    assert {"PG_RUNTIME_SERVICE_PASSWORD", "PG_RUNTIME_MIGRATOR_PASSWORD", "PG_ADMIN_PASSWORD", "QDRANT_API_KEY"} <= set(values)
    assert set(bundle.environment(["RUNTIME_OPERATOR_TOKEN"])) == {"RUNTIME_OPERATOR_TOKEN"}
    assert "PASSWORD" not in repr(bundle)


@pytest.mark.skipif(os.name != "nt", reason="Windows local journal")
def test_corrupt_journal_releases_operator_lock(tmp_path):
    path = tmp_path / "stores.json"
    path.write_text(json.dumps({"schema_version": "1", "deployment_id": "not-owned"}))
    for _ in range(2):
        with pytest.raises(ProfileError, match="deployment_state_identity"):
            with LocalState(tmp_path):
                pass
