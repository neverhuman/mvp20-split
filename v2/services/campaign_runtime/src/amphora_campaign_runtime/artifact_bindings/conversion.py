"""Finite typed conversion with injected public I/O; all output remains tentative."""

import json
from decimal import Decimal

from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import GraphBinding

from ..compiler.shapes import SchemaIdentity
from ..coordinator.values import BoundValues, ensure
from ..lifecycle.model import TransitionError
from .encoding import payload
from .model import BindingBudget


class Conversion:
    def __init__(self, binding, scope, schemas, peer):
        self.binding, self.scope, self.schemas, self.peer = binding, scope, schemas, peer
        self.budget = BindingBudget(binding.node.limits)
        self.cache = {}

    def schema(self, reference, value):
        self.schemas.require(SchemaIdentity.from_wire(reference), "binding").validate(value)

    def read(self, reference, slot):
        ensure(reference.scope == self.scope and reference.media_type == "application/json", "binding_artifact_scope_or_media")
        key = reference.model_dump_json()
        if key not in self.cache:
            self.budget.add(artifacts=1, size=reference.size_bytes)
            self.peer.protect(reference, slot)
            data = self.peer.read(reference)
            self.schema(reference.schema_ref, data)
            self.cache[key] = data
        return self.cache[key]

    def publish(self, value, shape, slot):
        self.schema(shape.schema_ref, value)
        body = payload(value)
        self.budget.add(artifacts=1, size=len(body))
        reference = self.peer.publish(body, shape.schema_ref, slot)
        ensure(reference.scope == self.scope and reference.schema_ref == shape.schema_ref
               and reference.media_type == "application/json", "binding_publication_mismatch")
        self.peer.protect(reference, slot)
        return {"kind": "artifact", "artifact": reference.model_dump(mode="json"),
                "representation": shape.representation, "unit": shape.unit}

    def scalar(self, value, shape):
        kind = shape.scalar
        if kind == "integer" and isinstance(value, Decimal) and value.is_finite() and value == value.to_integral_value():
            value = int(value)
        valid = {"boolean": type(value) is bool, "integer": type(value) is int,
                 "number": type(value) in {int, Decimal}, "string": type(value) is str}[kind]
        ensure(valid, "binding_scalar_type")
        if kind == "number":
            value = format(Decimal(value), "f")
        return {"kind": kind, "value": value, **({"unit": shape.unit} if kind in {"integer", "number"} else {})}

    def project(self):
        node = self.binding.node
        source = self.binding.values.values["source"]
        value = self.read(source.artifact, "source")
        for step in node.path:
            ensure((isinstance(step, str) and isinstance(value, dict) and step in value)
                   or (type(step) is int and isinstance(value, list) and step < len(value)), "binding_path_missing")
            value = value[step]
        shape = node.output.value_type
        if shape.kind == "scalar":
            return self.scalar(value, shape)
        ensure(isinstance(value, list), "binding_array_required")
        self.budget.add(items=len(value))
        values = []
        for index, item in enumerate(value):
            slot = "member:" + str(index)
            if node.mode == "values":
                values.append(self.scalar(item, shape.item))
            elif node.mode == "items":
                values.append(self.publish(item, shape.item, slot))
            else:
                try:
                    reference = ArtifactRef.model_validate(item)
                except ValueError as error:
                    raise TransitionError("binding_reference_invalid") from error
                ensure(reference.schema_ref == shape.item.schema_ref and reference.media_type == shape.item.media_type,
                       "binding_reference_type")
                self.read(reference, slot)
                values.append({"kind": "artifact", "artifact": reference.model_dump(mode="json"),
                    "representation": shape.item.representation, "unit": shape.item.unit})
        return {"kind": "collection", "items": values}

    def materialized(self, value, mode, slot):
        if value.kind == "missing":
            return value.model_dump(mode="json")
        if value.kind == "collection":
            self.budget.add(items=len(value.items))
            return [self.materialized(item, mode, slot + ":" + str(index)) for index, item in enumerate(value.items)]
        if value.kind == "artifact":
            data = self.read(value.artifact, slot)
            return value.artifact.model_dump(mode="json") if mode == "references" else data
        ensure(mode == "inline", "binding_reference_source_required")
        return Decimal(value.value) if value.kind == "number" else value.value

    def run(self):
        node = self.binding.node
        if node.kind == "artifact_project":
            value = self.project()
        else:
            data = {field.name: self.materialized(self.binding.values.values[field.name], field.mode, "field:" + str(index))
                    for index, field in enumerate(sorted(node.fields, key=lambda field: field.name))}
            value = self.publish(data, node.output.value_type, "result")
        try:
            result = BoundValues((GraphBinding.model_validate_json(json.dumps({"port": node.output.name, "value": value})),))
        except ValueError as error:
            raise TransitionError("binding_output_invalid") from error
        return result.validate((node.output,), self.scope)
