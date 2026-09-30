"""Scoped compiler-review metadata for forms; Registry owns discovery and live eligibility."""

import base64
from types import MappingProxyType

from amphora_contracts_core import SchemaRef
from amphora_contracts_graph_runtime import DefinitionSchema, DefinitionUniverse

from ..compiler import SchemaIdentity
from ..compiler.catalog import binding_key
from .reads import DefinitionReadError


class DefinitionCatalog:
    def __init__(self, universes):
        if any(key != (value.scope.tenant_id, value.scope.project_id) for key, value in universes.items()):
            raise ValueError("definition_catalog_scope_mismatch")
        self.universes = MappingProxyType(dict(universes))

    def _require(self, principal, expected=None):
        principal.require("read")
        universe = self.universes.get((principal.scope.tenant_id, principal.scope.project_id))
        if universe is None:
            raise DefinitionReadError("definition_universe_unavailable")
        if expected is not None and universe.sha256 != expected:
            raise DefinitionReadError("definition_universe_changed")
        return universe

    def universe(self, principal):
        universe = self._require(principal)
        return DefinitionUniverse(scope=universe.scope, universe_sha256=universe.sha256,
            reviewed_tools=tuple(tool.lock for tool in sorted(universe.releases, key=lambda item: binding_key(item.lock.tool))),
            schemas=tuple(SchemaRef(**schema.identity.record()) for schema in sorted(universe.schemas,
                key=lambda item: (item.identity.name, item.identity.version, item.identity.digest))))

    def schema(self, principal, expected_universe, reference):
        universe = self._require(principal, expected_universe)
        identity = SchemaIdentity.from_wire(reference)
        for schema in universe.schemas:
            if schema.identity == identity:
                return DefinitionSchema(scope=universe.scope, universe_sha256=universe.sha256, reference=reference,
                    schema_bytes_base64=base64.b64encode(schema.source_bytes).decode("ascii"))
        raise DefinitionReadError("reviewed_schema_unavailable")
