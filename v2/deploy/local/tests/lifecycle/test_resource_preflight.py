import subprocess
from types import SimpleNamespace

import pytest
from amphora_deployment.lifecycle.processes import OwnerProcess
from amphora_deployment.profile import ProfileError


@pytest.mark.parametrize("returncode", [0, 2])
def test_runtime_preflight_is_public_owner_cli_and_fails_closed(monkeypatch, returncode):
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=returncode)
    monkeypatch.setattr(subprocess, "run", run)
    if returncode:
        with pytest.raises(ProfileError, match="runtime_resource_preflight_failed"):
            OwnerProcess._resource_preflight("python", "runtime.json", {"AMPHORA_TEST": "value"})
    else:
        OwnerProcess._resource_preflight("python", "runtime.json", {"AMPHORA_TEST": "value"})
    args, options = calls[0]
    assert args == ["python", "-I", "-m", "amphora_campaign_runtime", "resource-preflight", "--config", "runtime.json"]
    assert options["timeout"] == 45 and options["stdout"] == subprocess.DEVNULL
    assert options["env"]["AMPHORA_TEST"] == "value" and "PYTHONPATH" not in options["env"]


def test_unavailable_owner_preflight_refuses_start(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("preflight", 45)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(ProfileError, match="runtime_resource_preflight_failed"):
        OwnerProcess._resource_preflight("python", "runtime.json", {})
