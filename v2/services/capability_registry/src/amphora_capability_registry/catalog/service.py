"""Authenticated registry application boundary with atomic command/audit receipts."""

import json

from ..descriptors.identity import ReleaseConflict
from ..persistence.store import CommandStore
from .inventory import Inventory, deployment_row, deployment_wire
from .model import RegistryDenied
from .releases import Releases, list_releases, read_release
from .resolution import Resolver


class Registry:
    def __init__(self, engine, resources, permissions, structural=None):
        self.engine = engine
        self.commands = CommandStore(engine)
        self.releases, self.inventory = Releases(structural), Inventory()
        self.resolver = Resolver(resources, permissions, structural)

    def execute(self, principal, command):
        action = command.identity.command_family.removeprefix("registry.")
        raw = json.loads(command.canonical_bytes)["payload"]

        def perform(connection, factory):
            try:
                # Expected rejection also rolls back any partial owner mutation.
                with connection.begin_nested():
                    if action == "register":
                        return self.releases.register(connection, principal.scope, raw, factory)
                    if action in {"activate", "drain", "revoke"}:
                        return self.releases.change(connection, principal.scope, action, raw, factory)
                    if action == "deploy":
                        return self.inventory.deploy(connection, principal.scope, raw, factory)
                    if action in {"drain_deployment", "revoke_deployment"}:
                        return self.inventory.change(connection, principal.scope, action, raw, factory)
                    if action == "heartbeat":
                        return self.inventory.heartbeat(connection, principal, raw, factory)
                    if action == "resolve":
                        return self.resolver.resolve(connection, principal.scope, raw, factory)
                    raise RegistryDenied("unknown_family")
            except (RegistryDenied, ReleaseConflict) as error:
                return factory.rejected(str(error))
        return self.commands.apply(principal, command, perform)

    def read_release(self, principal, digest):
        if "read" not in principal.actions:
            raise RegistryDenied("action_denied")
        with self.engine.connect() as connection:
            return read_release(connection, principal.scope, digest).to_wire(principal.scope)

    def read_deployment(self, principal, deployment_id):
        if "read" not in principal.actions:
            raise RegistryDenied("action_denied")
        with self.engine.connect() as connection:
            return deployment_wire(principal.scope, deployment_row(connection, principal.scope, deployment_id))

    def list_releases(self, principal, *, limit=50, after=None, capability_id=None, release=None):
        if "read" not in principal.actions:
            raise RegistryDenied("action_denied")
        with self.engine.connect() as connection:
            return list_releases(connection, principal.scope, limit=limit, after=after, capability_id=capability_id, release=release)
