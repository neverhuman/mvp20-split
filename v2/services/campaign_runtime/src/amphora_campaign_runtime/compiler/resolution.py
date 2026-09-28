"""Scope-local source and finite predicate checking; no artifact reads or evaluation."""

from .errors import require
from .shapes import ArtifactShape, CollectionShape, ScalarShape, SchemaIdentity, from_wire


class SchemaUsage:
    def __init__(self, catalog):
        self.catalog, self.identities = catalog, set()

    def check(self, shape, location):
        if isinstance(shape, CollectionShape):
            self.check(shape.item, location)
        elif isinstance(shape, ArtifactShape):
            self.catalog.require(shape.schema, location)
            self.identities.add(shape.schema)
        return shape


class SourceResolver:
    def __init__(self, scope, inputs, interfaces, topology, usage):
        self.scope = scope
        self.inputs = {port.name: port.shape for port in inputs}
        self.interfaces, self.topology, self.usage = interfaces, topology, usage

    def resolve(self, source, node_id, location, *, member=False, results=None):
        kind = source.kind
        if kind == "input":
            require(source.name in self.inputs, "unknown_scope_input", location)
            return self.inputs[source.name]
        if kind == "output":
            allowed = self.topology.ancestors(node_id) if member else self.topology.flows[node_id].guaranteed
            require(source.node_id in allowed, "unavailable_output", location)
            outputs = {port.name: port.shape for port in self.interfaces[source.node_id].outputs}
            require(source.port in outputs, "unknown_output_port", location)
            return outputs[source.port]
        if kind == "result":
            require(results is not None and source.name in results, "unavailable_scope_result", location)
            return results[source.name]
        if kind == "artifact":
            require(source.artifact.scope == self.scope, "artifact_scope_mismatch", location)
            shape = ArtifactShape(SchemaIdentity.from_wire(source.artifact.schema_ref), source.representation,
                                  source.unit, source.artifact.media_type)
            return self.usage.check(shape, location)
        return ScalarShape(kind, getattr(source, "unit", "1"))

    def bindings(self, bindings, expected, node_id, location, *, optional=()):
        supplied = {binding.port: binding.source for binding in bindings}
        expected = {port.name: port.shape for port in expected}
        require(len(supplied) == len(bindings), "duplicate_binding", location)
        require(set(supplied) <= set(expected), "unknown_binding", location)
        require(set(expected) - set(optional) <= set(supplied), "missing_binding", location)
        for name, source in supplied.items():
            actual = self.resolve(source, node_id, location + "." + name)
            require(expected[name].accepts(actual), "binding_type_mismatch", location + "." + name)

    def predicate(self, predicate, node_id, location, *, results=None):
        pending, count = [(predicate, 0)], 0
        while pending:
            value, depth = pending.pop()
            count += 1
            require(depth <= 16 and count <= 256, "predicate_complexity_limit", location)
            if value.kind in {"all", "any"}:
                pending.extend((child, depth + 1) for child in value.predicates)
            elif value.kind == "not":
                pending.append((value.predicate, depth + 1))
            elif value.kind == "compare":
                left = self.resolve(value.left.source, node_id, location, results=results)
                if isinstance(left, ArtifactShape):
                    require(left.media_type == "application/json", "projection_media_type", location)
                    left = self.usage.catalog.require(left.schema, location).project(value.left.path, left.unit, location)
                else:
                    require(isinstance(left, ScalarShape) and not value.left.path, "invalid_scalar_projection", location)
                require(left == from_wire(value.left.value_type, location), "projection_type_mismatch", location)
                right = ScalarShape(value.right.kind, getattr(value.right, "unit", "1"))
                require(left.accepts(right) or right.accepts(left), "predicate_type_mismatch", location)
                require(value.operator in {"eq", "ne"} or left.name in {"integer", "number"},
                        "ordered_comparison_not_numeric", location)
