import pytest
from amphora_numeric_affine.adapter import execute
from amphora_tool_protocol import ProtocolError, ToolInputRejected


def test_adapter_preserves_output_and_safe_failure():
    assert execute(b'{"values":[2],"a":3,"b":-1}') == b'{"schema_version":"1","values":[5.0]}'
    with pytest.raises(ToolInputRejected, match="^invalid_numeric_parameters$"):
        execute(b'{"values":["private"],"a":3,"b":-1}')


def test_worker_cli_marks_incomplete_execution_separately(monkeypatch, capsys):
    import amphora_numeric_affine.__main__ as cli
    monkeypatch.setattr("sys.argv", ["amphora-numeric-affine", "worker", "--config", "fixture.json"])
    def unavailable(*_args):
        raise ProtocolError("private owner diagnostic")
    monkeypatch.setattr(cli, "run_worker", unavailable)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 3
    output = capsys.readouterr()
    assert output.out == "" and output.err == "worker_execution_incomplete\n"
