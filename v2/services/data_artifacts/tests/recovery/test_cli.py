import json
import sys
from types import SimpleNamespace

import pytest
from amphora_data_artifacts.recovery import __main__ as cli


@pytest.mark.parametrize('status,expected', [('verified', 0), ('failed', 3), ('incomplete', 2)])
def test_create_once_safe_results_and_host_drain(tmp_path, monkeypatch, capsys, status, expected):
    output, inventory = tmp_path / 'summary.json', tmp_path / 'inventory.jsonl'
    closed = []
    host = SimpleNamespace(uploads=SimpleNamespace(commands=SimpleNamespace(engine=None)),
                           storage=None, close=lambda: closed.append(True))
    monkeypatch.setattr(cli.Host, 'load', lambda _: host)
    def run(self, *, inventory):
        if status == 'incomplete':
            raise RuntimeError('sensitive-driver-content')
        inventory.write('{}\n')
        return {'status': status}
    monkeypatch.setattr(cli.CatalogAudit, 'run', run)
    monkeypatch.setattr(sys, 'argv', ['audit', '--config', 'fixture', '--output', str(output),
                                     '--inventory-output', str(inventory)])
    assert cli.main() == expected
    assert closed == [True]
    assert 'sensitive' not in capsys.readouterr().out
    if status != 'incomplete':
        assert json.loads(output.read_text())['status'] == status
    else:
        assert output.read_text() == ''
    before = output.read_bytes()
    assert cli.main() == 2  # never overwrite an earlier/partial audit
    assert output.read_bytes() == before
