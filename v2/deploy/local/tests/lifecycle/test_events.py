import json

import pytest

from amphora_deployment.lifecycle import LifecycleEvents
from amphora_deployment.profile import ProfileError


def test_logs_remain_bounded_and_reject_free_text(tmp_path):
    events = LifecycleEvents(tmp_path, limit=1024)
    for _ in range(100):
        events.emit('runtime', 'started', pid=123)
    files = list(tmp_path.iterdir())
    assert len(files) == 2
    assert all(path.stat().st_size <= 1024 for path in files)
    for path in files:
        for line in path.read_text().splitlines():
            assert set(json.loads(line)) == {'at', 'owner', 'event', 'pid', 'exit_code'}
    for owner, event in [('secret', 'started'), ('runtime', 'password=secret')]:
        with pytest.raises(ProfileError):
            events.emit(owner, event)
    with pytest.raises(ProfileError):
        events.emit('runtime', 'exited', exit_code='secret')
