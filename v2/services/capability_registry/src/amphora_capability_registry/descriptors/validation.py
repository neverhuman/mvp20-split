"""Pure descriptor consistency; suitability, permissions and health are separate."""

from dataclasses import dataclass

from amphora_contracts_core import Finding
from amphora_contracts_tools import StructuralAssessment


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    location: str
    message: str

    def to_wire(self):
        return Finding(code=self.code, location=self.location, message=self.message)


@dataclass(frozen=True, slots=True)
class ValidationReport:
    issues: tuple[Issue, ...]

    @property
    def valid(self):
        return not self.issues

    def to_wire(self):
        return StructuralAssessment(status="valid" if self.valid else "invalid",
                                    findings=tuple(issue.to_wire() for issue in self.issues))


class DescriptorValidator:
    def validate(self, descriptor):
        issues = []

        def issue(code, location, message):
            if len(issues) < 128:
                issues.append(Issue(code, location, message))

        def unique(values, location):
            if len(set(values)) != len(values):
                issue("duplicate_declaration", location, "Declarations must be unique")

        tool = descriptor.tool
        if not tool.purpose.strip():
            issue("missing_purpose", "tool.purpose", "Purpose must contain non-whitespace text")
        if not tool.outputs:
            issue("missing_output", "tool.outputs", "A result-producing tool must declare an output")
        for side in ("inputs", "outputs"):
            ports = getattr(tool, side)
            unique([port.name for port in ports], "tool." + side)
            for index, port in enumerate(ports):
                if not port.unit.strip() or port.unit != port.unit.strip():
                    issue("invalid_unit", f"tool.{side}.{index}.unit", "Explicit normalized unit required; no implicit conversion")
        unique(tool.applicability, "tool.applicability")
        if any(not value.strip() or value != value.strip() for value in tool.applicability):
            issue("invalid_applicability", "tool.applicability", "Explicit normalized applicability required")
        for name in ("examples", "anti_examples"):
            if any(not value.strip() for value in getattr(descriptor, name)):
                issue("empty_example", name, "Example must contain non-whitespace text")
        unique(descriptor.resources.architectures, "resources.architectures")
        unique(descriptor.resources.operating_systems, "resources.operating_systems")
        if descriptor.egress.mode == "allowlist":
            unique(descriptor.egress.hosts, "egress.hosts")
        checkpoint = descriptor.checkpoint
        unique(checkpoint.readable_schema_sha256, "checkpoint.readable_schema_sha256")
        if checkpoint.mode == "none":
            if tool.checkpoint_schema is not None or checkpoint.readable_schema_sha256:
                issue("checkpoint_contract_mismatch", "checkpoint", "Stateless release cannot claim checkpoint schemas")
        elif tool.checkpoint_schema is None or tool.checkpoint_schema.sha256 not in checkpoint.readable_schema_sha256:
            issue("checkpoint_contract_mismatch", "checkpoint", "Checkpoint writer schema must be explicitly readable")
        return ValidationReport(tuple(issues))
