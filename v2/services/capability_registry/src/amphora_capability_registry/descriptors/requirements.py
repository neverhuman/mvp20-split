"""Owned capability needs and finite deployment-policy allowances."""

from dataclasses import dataclass

from amphora_contracts_core import Scope

from .identity import SchemaIdentity


@dataclass(frozen=True, slots=True)
class PortRequirement:
    name: str
    schema: SchemaIdentity
    representation: str
    unit: str

    @classmethod
    def from_port(cls, port):
        return cls(port.name, SchemaIdentity.from_ref(port.schema_ref), port.representation, port.unit)


@dataclass(frozen=True, slots=True)
class CapabilityNeed:
    scope: Scope
    context: str
    inputs: tuple[PortRequirement, ...]
    outputs: tuple[PortRequirement, ...]

    @classmethod
    def for_tool(cls, scope, context, tool):
        return cls(scope, context, tuple(PortRequirement.from_port(port) for port in tool.inputs),
                   tuple(PortRequirement.from_port(port) for port in tool.outputs))


@dataclass(frozen=True, slots=True)
class ResourceAllowance:
    architecture: str
    operating_system: str
    cpu_millicores: int
    memory_mib: int
    gpu_count: int
    timeout_seconds: int
    max_parallel_invocations: int
    max_batch_size: int

    def __post_init__(self):
        if self.architecture not in {"x86_64", "aarch64"} or self.operating_system not in {"linux", "windows"}:
            raise ValueError("Unknown supported host profile")
        for name in ("cpu_millicores", "memory_mib", "timeout_seconds", "max_parallel_invocations", "max_batch_size", "gpu_count"):
            value = getattr(self, name)
            minimum = 0 if name == "gpu_count" else 1
            if type(value) is not int or not minimum <= value <= 9007199254740991:
                raise ValueError("Finite nonnegative resource allowance required")

    def rejections(self, resources):
        reasons = []
        if self.architecture not in resources.architectures:
            reasons.append("architecture_unsupported")
        if self.operating_system not in resources.operating_systems:
            reasons.append("operating_system_unsupported")
        for name in ("cpu_millicores", "memory_mib", "gpu_count", "timeout_seconds", "max_parallel_invocations", "max_batch_size"):
            if getattr(resources, name) > getattr(self, name):
                reasons.append("resource_limit_" + name)
        return tuple(reasons)


def compatibility_rejections(descriptor, need):
    reasons = []
    for side in ("inputs", "outputs"):
        actual = {port.name: port for port in getattr(descriptor.tool, side)}
        wanted = {port.name: port for port in getattr(need, side)}
        if len(wanted) != len(getattr(need, side)):
            reasons.append("duplicate_required_port")
        for name, requirement in wanted.items():
            port = actual.get(name)
            if port is None:
                reasons.append("required_port_missing")
                continue
            if SchemaIdentity.from_ref(port.schema_ref) != requirement.schema:
                reasons.append("schema_incompatible")
            if port.representation != requirement.representation:
                reasons.append("representation_incompatible")
            if port.unit != requirement.unit:
                reasons.append("unit_incompatible")
        if side == "inputs" and any(port.required and port.name not in wanted for port in actual.values()):
            reasons.append("required_input_unsupplied")
    return tuple(dict.fromkeys(reasons))
