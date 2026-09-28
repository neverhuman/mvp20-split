"""Bounded committed graph values own compatibility and explicit artifact projection."""

from dataclasses import dataclass
from types import MappingProxyType

from amphora_contracts_graph_runtime import GraphBinding

from ..compiler.shapes import ArtifactShape, CollectionShape, ScalarShape, SchemaIdentity, ports
from ..lifecycle.model import TransitionError


def ensure(condition, code):
    if not condition:
        raise TransitionError(code)


def compatible(value, shape, scope):
    if value.kind == "collection":
        return (isinstance(shape, CollectionShape) and len(value.items) <= shape.maximum and
                all(shape.missing if item.kind == "missing" else compatible(item, shape.item, scope) for item in value.items))
    if value.kind == "artifact":
        actual = ArtifactShape(SchemaIdentity.from_wire(value.artifact.schema_ref), value.representation,
                               value.unit, value.artifact.media_type)
        return isinstance(shape, ArtifactShape) and shape.accepts(actual) and value.artifact.scope == scope
    return isinstance(shape, ScalarShape) and shape.accepts(ScalarShape(value.kind, getattr(value, "unit", "1")))


@dataclass(frozen=True)
class BoundValues:
    bindings: tuple

    def __post_init__(self):
        ensure(len({binding.port for binding in self.bindings}) == len(self.bindings), "duplicate_graph_input")

    @property
    def values(self):
        return MappingProxyType({binding.port: binding.value for binding in self.bindings})

    def validate(self, expected, scope):
        declarations = ports(expected, "inputs")
        ensure(set(self.values) == {port.name for port in declarations}, "graph_input_ports_mismatch")
        ensure(all(compatible(self.values[port.name], port.shape, scope) for port in declarations), "graph_input_type_mismatch")
        return self

    def record(self):
        return [binding.model_dump(mode="json") for binding in sorted(self.bindings, key=lambda value: value.port)]

    @classmethod
    def from_records(cls, records):
        import json
        return cls(tuple(GraphBinding.model_validate_json(json.dumps(record)) for record in records))
