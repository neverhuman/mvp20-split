from pathlib import Path

import pytest
from amphora_deployment.profile import ProfileError
from amphora_deployment.workers.recipes import NATIVE_RECIPES, WorkerScope


@pytest.mark.parametrize('name', list(NATIVE_RECIPES))
def test_closed_commands_keep_scope_and_bounded_owner_operation(tmp_path, name):
    recipe = NATIVE_RECIPES[name]
    scope = WorkerScope('actor', 'tenant', 'project') if recipe.scoped else None
    command = recipe.command(tmp_path / 'python.exe', tmp_path / 'worker.json', scope)
    assert command[1:4] == ('-I', '-m', recipe.module)
    assert command[4] == recipe.action
    assert '--time-budget' in command if recipe.scoped else '--seconds' in command
    window = command[command.index('--time-budget' if recipe.scoped else '--seconds') + 1]
    assert window == ('20' if name == 'planning-curation' else '2')
    if not recipe.scoped:
        assert command[command.index('--interval') + 1] == '1'
    assert 'serve' not in command
    with pytest.raises(ProfileError, match='scope_binding'):
        recipe.command(tmp_path / 'python.exe', tmp_path / 'worker.json',
                       None if recipe.scoped else WorkerScope('a', 't', 'p'))


def test_relative_configuration_and_invalid_scope_rejected(tmp_path):
    with pytest.raises(ProfileError, match='absolute_paths'):
        NATIVE_RECIPES['planning-checkpoint'].command(tmp_path / 'python.exe', Path('worker.json'))
    with pytest.raises(ProfileError, match='worker_scope'):
        WorkerScope('--inject', 'tenant', 'project')
