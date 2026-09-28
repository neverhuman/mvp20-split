"""Committed local values resolve sources; unavailable/missing data never becomes a default."""

from dataclasses import dataclass
from decimal import Decimal

from amphora_contracts_graph_runtime import GraphBinding, NumberValue
from amphora_contracts_runtime import PreparedInvocation
from amphora_contracts_tools import InputBinding

from ..lifecycle.model import TransitionError
from .values import BoundValues, ensure


@dataclass(frozen=True)
class ValueEnvironment:
    inputs: BoundValues
    outputs: object
    results: BoundValues | None = None

    def source(self, value):
        if value.kind == "input":
            result = self.inputs.values.get(value.name)
        elif value.kind == "output":
            node = self.outputs.get(value.node_id)
            result = None if node is None else node.values.get(value.port)
        elif value.kind == "result":
            result = None if self.results is None else self.results.values.get(value.name)
        else:
            result = value
        ensure(result is not None, "graph_value_unavailable")
        if result.kind == "number" and not isinstance(result.value, str):
            return NumberValue(kind="number", value=format(Decimal(str(result.value)), "f"), unit=result.unit)
        return result

    def bind(self, bindings):
        return BoundValues(tuple(GraphBinding(port=binding.port, value=self.source(binding.source)) for binding in bindings))


@dataclass(frozen=True)
class InvocationIntent:
    address: object
    node: object
    environment: ValueEnvironment

    def prepared(self):
        values = self.environment.bind(self.node.inputs)
        inputs = []
        for binding in values.bindings:
            if binding.value.kind != "artifact":
                raise TransitionError("tool_artifact_input_required")
            inputs.append(InputBinding(port=binding.port, artifact=binding.value.artifact))
        checkpoint = None if self.node.checkpoint is None else self.environment.source(self.node.checkpoint)
        ensure(checkpoint is None or checkpoint.kind == "artifact", "tool_artifact_checkpoint_required")
        return PreparedInvocation(node_id=self.node.node_id, activation_id=self.address.key,
            invocation_id=self.address.key, tool=self.node.tool, inputs=tuple(inputs),
            checkpoint=None if checkpoint is None else checkpoint.artifact, timeout_seconds=self.node.timeout_seconds)
