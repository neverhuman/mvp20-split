"""CLI routing with explicit streams; live worker transport is a separate gate."""

import io
from types import SimpleNamespace

import pytest
from amphora_synthetic_objectives_rebuilt import __main__ as cli
from amphora_synthetic_objectives_rebuilt.metadata import policy_bytes, schema_bytes


@pytest.fixture
def streams(monkeypatch):
    output, error = io.BytesIO(), io.StringIO()
    monkeypatch.setattr(cli, "sys", SimpleNamespace(stdout=SimpleNamespace(buffer=output), stderr=error, stdin=None))
    return output, error


@pytest.mark.parametrize("command", [["policy"], ["schema", "--kind", "input"],
                                    ["describe", "--image-sha256", "b" * 64]])
def test_metadata_dispatch(streams, command):
    assert cli.main(command) == 0
    assert streams[0].getvalue() and not streams[1].getvalue()
    if command == ["policy"]:
        assert streams[0].getvalue() == policy_bytes()
    if command[0] == "schema":
        assert streams[0].getvalue() == schema_bytes("input")


@pytest.mark.parametrize("oversized", [False, True])
def test_compute_dispatch(streams, monkeypatch, fixture_request, tmp_path, oversized):
    policy = tmp_path / "policy.json"
    policy.write_bytes(policy_bytes())
    body = b"x" * (cli.MAX_BYTES + 1) if oversized else fixture_request.model_dump_json().encode()
    monkeypatch.setattr(cli.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(body)))
    assert cli.main(["compute", "--image-sha256", "b" * 64, "--policy-file", str(policy)]) == (2 if oversized else 0)
    assert bool(streams[0].getvalue()) != oversized


def test_missing_policy_safe_failure(streams, monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"private")))
    assert cli.main(["compute", "--image-sha256", "b" * 64, "--policy-file", str(tmp_path / "absent")]) == 2
    assert not streams[0].getvalue()
    assert streams[1].getvalue() == "invalid_synthetic_input_or_configuration\n"
