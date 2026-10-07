"""Actual TLS admission for five tool requests plus five simultaneous readiness probes."""

from contextlib import ExitStack

import pytest
from amphora_deployment.tool_access.load import ConnectionLoad

from .test_proxy import Owner, connection, servers


def test_default_listener_accepts_tool_and_readiness_concurrency(identity):
    with servers(identity, Owner) as (proxy, _), ExitStack() as clients:
        # Keep every established connection open to make overlap deterministic.
        # No payload, owner credential or provider traffic is needed for this boundary.
        for _ in range(10):
            client = connection(identity, proxy.server_port)
            clients.callback(client.close)
        assert proxy.load.snapshot()['peak'] == 10
        assert proxy.load.snapshot()['denied'] == 0


def test_explicit_capacity_denial_releases_no_unowned_slot(identity):
    with servers(identity, Owner, maximum_connections=2) as (proxy, _), ExitStack() as clients:
        for _ in range(2):
            client = connection(identity, proxy.server_port)
            clients.callback(client.close)
        with pytest.raises(OSError):
            connection(identity, proxy.server_port)
        assert proxy.load.snapshot() == {'limit': 2, 'active': 2, 'peak': 2, 'admitted': 2, 'denied': 1}


def test_load_accounting_recovers_capacity_without_resetting_denials():
    load = ConnectionLoad(1)
    assert load.acquire() and not load.acquire()
    load.release()
    assert load.acquire()
    load.release()
    assert load.snapshot() == {'limit': 1, 'active': 0, 'peak': 1, 'admitted': 2, 'denied': 1}
    with pytest.raises(RuntimeError, match='tool_tls_connection_release'):
        load.release()
