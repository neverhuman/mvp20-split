from types import SimpleNamespace

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.scientific_workers.journal import ContainerJournal
from amphora_deployment.scientific_workers.ownership import (
    journal_path,
    require_configured_pending,
    require_released,
)


def test_unresolved_container_blocks_migration_even_without_live_control_or_api(tmp_path):
    profile = SimpleNamespace(name='evolution-seed', fingerprint='b' * 64)
    deployment_id = 'a' * 32
    require_released(tmp_path, deployment_id)
    journal = ContainerJournal(journal_path(tmp_path, profile), deployment_id, profile.name, profile.fingerprint)
    journal.intent()
    for advance in (lambda: None, lambda: journal.created('c' * 64), journal.starting,
                    journal.started, lambda: journal.exited(0)):
        advance()
        with pytest.raises(ProfileError, match='migration_requires_reconciled_containers'):
            require_released(tmp_path, deployment_id)
    journal.released()
    require_released(tmp_path, deployment_id)


def test_new_composition_cannot_omit_an_old_pending_binding(tmp_path):
    old = SimpleNamespace(name='evolution-seed', fingerprint='b' * 64)
    new = SimpleNamespace(name='evolution-seed', fingerprint='c' * 64)
    journal = ContainerJournal(journal_path(tmp_path, old), 'a' * 32, old.name, old.fingerprint)
    journal.intent()
    require_configured_pending(tmp_path, 'a' * 32, [old])
    with pytest.raises(ProfileError, match='pending_binding_not_configured'):
        require_configured_pending(tmp_path, 'a' * 32, [new])
    journal.created('d' * 64)
    journal.starting()
    journal.exited(0)
    journal.released()
    require_configured_pending(tmp_path, 'a' * 32, [new])


def test_foreign_or_malformed_journal_is_not_ignored(tmp_path):
    profile = SimpleNamespace(name='evolution-seed', fingerprint='b' * 64)
    journal = ContainerJournal(journal_path(tmp_path, profile), 'a' * 32, profile.name, profile.fingerprint)
    journal.intent()
    with pytest.raises(ProfileError, match='journal_binding'):
        require_released(tmp_path, 'c' * 32)
    journal.path.rename(journal.path.with_name('unexpected.json'))
    with pytest.raises(ProfileError, match='retained_filename'):
        require_released(tmp_path, 'a' * 32)
