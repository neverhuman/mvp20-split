import socket

import pytest

from amphora_deployment.installation import OWNERS
from amphora_deployment.persistence.migrations import require_stopped
from amphora_deployment.profile import ProfileError


def test_live_service_binding_blocks_migration_before_any_database_command():
    with socket.socket() as server:
        server.bind(('127.0.0.1',0));server.listen(1)
        routes={'host':'127.0.0.1','ports':{name:server.getsockname()[1] for name in (*OWNERS,'gateway','supervisor')}}
        with pytest.raises(ProfileError,match='requires_stopped_services'):
            require_stopped(routes)


@pytest.mark.parametrize('routes',[None,{}, {'host':'0.0.0.0','ports':{}}, {'host':'127.0.0.1','ports':{}}])
def test_missing_or_foreign_network_scope_blocks_migration(routes):
    with pytest.raises(ProfileError):require_stopped(routes)
