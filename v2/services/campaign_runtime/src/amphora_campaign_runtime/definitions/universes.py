"""Scoped immutable union of reviewed host materials, never a discovery or eligibility grant."""

from types import MappingProxyType

from ..compiler.catalog import binding_key
from .validation import ValidationUniverse


def from_graphs(graphs):
    grouped = {}
    for plan, tools, schemas in graphs:
        key = (plan.scope.tenant_id, plan.scope.project_id)
        scope, releases, documents = grouped.setdefault(key, (plan.scope, {}, {}))
        for tool in tools:
            identity = binding_key(tool.lock.tool)
            if identity in releases and releases[identity] != tool:
                raise ValueError("conflicting_authoring_tool_pin")
            releases[identity] = tool
        for schema in schemas:
            if schema.identity in documents and documents[schema.identity].source_bytes != schema.source_bytes:
                raise ValueError("conflicting_authoring_schema_pin")
            documents[schema.identity] = schema
    return MappingProxyType({key: ValidationUniverse(scope, tuple(tools.values()), tuple(schemas.values()))
                             for key, (scope, tools, schemas) in grouped.items()})
