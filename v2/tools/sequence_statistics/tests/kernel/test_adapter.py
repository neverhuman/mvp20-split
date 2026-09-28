import pytest
from amphora_sequence_statistics.adapter import execute
from amphora_tool_protocol import ProtocolError, ToolInputRejected


@pytest.mark.parametrize("payload,reason", [
    (b'{"sequence":"AX","alphabet":"ACGT"}', "invalid_sequence_symbol"),
    (b'{"sequence":"A","alphabet":"AA"}', "duplicate_alphabet_symbol"),
    (b'{"sequence":"A","alphabet":""}', "invalid_sequence_parameters"),
])
def test_adapter_exposes_only_specific_safe_reason(payload, reason):
    with pytest.raises(ToolInputRejected, match="^" + reason + "$"):
        execute(payload)


def test_adapter_preserves_success():
    assert execute(b'{"sequence":"AA","alphabet":"AB"}') == (
        b'{"schema_version":"1","length":2,"counts":[{"symbol":"A","count":2},{"symbol":"B","count":0}]}')


def test_worker_cli_marks_incomplete_execution_separately(monkeypatch, capsys):
    import amphora_sequence_statistics.__main__ as cli
    monkeypatch.setattr("sys.argv", ["amphora-sequence-statistics", "worker", "--config", "fixture.json"])
    def unavailable(*_args):
        raise ProtocolError("private owner diagnostic")
    monkeypatch.setattr(cli, "run_worker", unavailable)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 3
    output = capsys.readouterr()
    assert output.out == "" and output.err == "worker_execution_incomplete\n"
