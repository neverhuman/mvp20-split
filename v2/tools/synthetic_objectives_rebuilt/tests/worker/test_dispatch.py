"""One-invocation SDK handoff, without claiming live peer acceptance."""

import io
from types import SimpleNamespace

import pytest
from amphora_synthetic_objectives_rebuilt import __main__ as cli
from amphora_synthetic_objectives_rebuilt.adapter import SyntheticWorkerAdapter
from amphora_tool_protocol import ProtocolError


@pytest.mark.parametrize("failed", [False, True])
def test_configured_public_sdk_handoff(monkeypatch, failed):
    output, error = io.BytesIO(), io.StringIO()
    monkeypatch.setattr(cli.sys, "stdout", SimpleNamespace(buffer=output))
    monkeypatch.setattr(cli.sys, "stderr", error)
    calls = []
    def invoke(path, factory, compute):
        assert path == "explicit.json"
        assert isinstance(factory.__self__, SyntheticWorkerAdapter)
        assert compute.__self__ is factory.__self__
        assert factory("b" * 64).tool.binding.release == "0.4.0"
        calls.append(path)
        if failed:
            raise ProtocolError("private-test-diagnostic")
        return {"status": "no_eligible_work"}
    monkeypatch.setattr(cli, "run_multi_input_worker", invoke)
    assert cli.main(["worker", "--config", "explicit.json"]) == (2 if failed else 0)
    assert len(calls) == 1
    assert output.getvalue() == (b"" if failed else b'{"status":"no_eligible_work"}')
    assert "private" not in error.getvalue()
