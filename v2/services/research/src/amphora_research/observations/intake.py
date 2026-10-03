"""Bound intake intent and immutable terminals; no peer calls or scientific verdict authority."""
import json
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, Identifier, Scope
from amphora_contracts_research import (
    LabIntakeFailed,
    LabIntakePending,
    LabIntakeRequest,
    LabIntakeResolved,
    LabIntakeStatus,
    LabReturnProfile,
)
from pydantic import TypeAdapter

from .identity import require
from .report_wire import to_resolution
from .reports import ConfiguredLabReturn
from .resolution import ResolvedLabReport

IDENTIFIER = TypeAdapter(Identifier)


def canonical(value, limit):
    content = json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
    require(len(content) <= limit,"lab_intake_byte_limit")
    return content


@dataclass(frozen=True, slots=True)
class IntakeIntent:
    configured: ConfiguredLabReturn
    request: LabIntakeRequest
    actor: str
    content: bytes

    @classmethod
    def bind(cls, configured, request, actor, scope):
        require(type(configured) is ConfiguredLabReturn,"lab_profile_required")
        require(type(request) is LabIntakeRequest,"lab_intake_request_required")
        configured = ConfiguredLabReturn(configured.document)
        request = LabIntakeRequest.model_validate_json(request.model_dump_json())
        IDENTIFIER.validate_python(actor,strict=True)
        require(type(scope) is Scope and request.profile.scope == scope and request.report.scope == scope,
                "lab_intake_scope_mismatch")
        require(request.profile == configured.reference,"lab_intake_profile_mismatch")
        content = canonical({"format":"research.lab-intake.v1","request":request.model_dump(mode="json"),
            "profile":configured.document.model_dump(mode="json"),"actor":actor},2097152)
        return cls(configured,request,actor,content)

    @classmethod
    def restore(cls, content):
        raw = json.loads(content)
        require(raw["format"] == "research.lab-intake.v1","lab_intake_storage_format")
        configured = ConfiguredLabReturn(LabReturnProfile.model_validate_json(json.dumps(raw["profile"])))
        request = LabIntakeRequest.model_validate_json(json.dumps(raw["request"]))
        return cls.bind(configured,request,raw["actor"],request.profile.scope)

    @property
    def key(self):
        scope = self.request.profile.scope
        return {"tenant":scope.tenant_id,"project":scope.project_id,"id":self.request.intake_id}

    def pending(self):
        return self.status(LabIntakePending(status="pending"))

    def status(self, outcome):
        return LabIntakeStatus(wire_version="1",request=self.request,actor_id=self.actor,outcome=outcome)

    def resolve(self, resolved):
        require(type(resolved) is ResolvedLabReport,"lab_intake_resolution_required")
        report = resolved.report
        require(report.configured.document == self.configured.document and report.source == self.request.report,
                "lab_intake_resolution_mismatch")
        inputs = resolved.inputs
        require(type(inputs) is tuple and 0 < len(inputs) <= 128,"lab_intake_input_limit")
        require(all(type(item) is ArtifactRef for item in inputs),"lab_intake_input_type")
        require(all(item.scope == self.request.profile.scope for item in inputs),"lab_intake_input_scope")
        require(len({item.artifact_id for item in inputs}) == len(inputs),"lab_intake_input_duplicate")
        require({report.source,report.raw_report,*report.context_sources} <= set(inputs),"lab_intake_input_missing")
        references = tuple(item.observation.identity.reference for item in report.entries)
        require(len(references) <= 64 and len({item.observation_id for item in references}) == len(references),
                "lab_intake_observation_limit_or_duplicate")
        require(all(item.observation.source == report.source for item in report.entries),"lab_intake_observation_source")
        ordered = tuple(sorted(inputs,key=lambda item:item.artifact_id))
        status = self.status(LabIntakeResolved(status="resolved",resolution=to_resolution(report)))
        return IntakeTerminal.prepare(status,ordered)

    def fail(self, reason):
        # The workflow decides which operational errors are terminal; this is never a scientific negative.
        return IntakeTerminal.prepare(self.status(LabIntakeFailed(status="failed",reason=reason)),())


@dataclass(frozen=True, slots=True)
class IntakeTerminal:
    status: LabIntakeStatus
    inputs: tuple
    content: bytes

    @classmethod
    def prepare(cls, status, inputs):
        require(status.outcome.status != "pending","lab_intake_terminal_required")
        content = canonical({"format":"research.lab-terminal.v1","status":status.model_dump(mode="json"),
            "inputs":[item.model_dump(mode="json") for item in inputs]},8388608)
        return cls(status,inputs,content)
