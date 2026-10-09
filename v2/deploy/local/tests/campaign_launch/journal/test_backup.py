import shutil
import sqlite3
import pytest

from amphora_deployment.campaign_launch.backup import require_launches_drained
from amphora_deployment.campaign_launch.intent import LaunchError
from amphora_deployment.campaign_launch.journal import LaunchJournal


def test_backup_guard_blocks_active_launch_and_cold_copy_preserves_history(tmp_path, make_intent, clock):
    root = tmp_path / 'original'
    journal = LaunchJournal(root / 'campaign-launches')
    state = journal.submit(make_intent(), lambda i: None, now=clock)
    with pytest.raises(LaunchError, match='launch_backup_requires_drain'):
        require_launches_drained(root)
    state = journal.change(state.intent.key, state.revision, lambda s: s.move('rejected', clock(), 'preflight_failed'))
    assert require_launches_drained(root) == 1
    restored = tmp_path / 'restored'
    shutil.copytree(root, restored)
    assert require_launches_drained(restored) == 1
    reopened = LaunchJournal(restored / 'campaign-launches')
    assert reopened.get(state.intent.key) == state
    assert reopened.submit(state.intent, lambda i: None, now=clock) == state


@pytest.mark.parametrize('column,value', [('revision', 100), ('active', None), ('actor', 'changed')])
def test_journal_reopen_rejects_index_metadata_corruption(tmp_path, make_intent, clock, column, value):
    journal = LaunchJournal(tmp_path)
    journal.submit(make_intent(), lambda i: None, now=clock)
    with sqlite3.connect(journal.path) as db:
        db.execute('UPDATE launches SET ' + column + '=?', (value,))
    with pytest.raises(LaunchError, match='launch_journal_corrupt'):
        LaunchJournal(tmp_path)


def test_legacy_installation_backup_guard_creates_no_state(tmp_path):
    assert require_launches_drained(tmp_path) == 0
    assert not (tmp_path / 'campaign-launches').exists()
