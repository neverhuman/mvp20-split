"""Item findings and bounded candidate outputs, never accepted outcomes."""

from dataclasses import dataclass

from amphora_contracts_core import Finding
from amphora_contracts_knowledge import GraphChangeProposal


@dataclass(frozen=True)
class ValidationResult:
    proposal_bytes: bytes | None
    findings: tuple[Finding, ...]
    withheld: tuple[str, ...]
    outcome: str

    @property
    def validation(self):
        return "quotation_and_structure_only"

    def proposal(self):
        return None if self.proposal_bytes is None else GraphChangeProposal.model_validate_json(self.proposal_bytes)


class Findings:
    def __init__(self):
        self.records, self.withheld = [], set()

    def add(self, path, code, *, withhold=True):
        finding = Finding(code=code, location=path, message=code.replace("_", " "))
        if finding not in self.records:
            self.records.append(finding)
        if withhold:
            self.withheld.add(path)

    def check(self, path, operation):
        try:
            return operation()
        except ValueError as error:
            # Only controlled domain guards belong here, never external errors
            # or Pydantic diagnostics containing candidate text.
            code = str(error)
            if not code or len(code) > 128 or not all(c.islower() or c == "_" for c in code):
                raise
            self.add(path, code)
            return None

    def result(self, proposal_bytes=None, *, abstained=False):
        outcome = "abstained" if abstained else (
            "partial" if proposal_bytes is not None and self.withheld else
            "proposed" if proposal_bytes is not None else "unresolved")
        return ValidationResult(proposal_bytes, tuple(self.records), tuple(sorted(self.withheld)), outcome)
