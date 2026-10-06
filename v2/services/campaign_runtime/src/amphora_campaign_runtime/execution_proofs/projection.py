from dataclasses import dataclass

from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_runtime import CompletionRecord, PreparedInvocation


class ProducerProofError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProducerSnapshot:
    invocation: PreparedInvocation
    completion: CompletionRecord
    worker_id: str
    attempt_id: str
    fence: int

    def __post_init__(self):
        report = self.completion
        if (not report.canonical_result or report.result.outcome.status != 'succeeded'
            or self.invocation.activation_id != report.activation_id
            or self.invocation.invocation_id != report.result.invocation_id
            or self.attempt_id != report.result.attempt_id or self.fence != report.result.fence):
            raise ProducerProofError('producer_identity_inconsistent')
        references = [item.artifact for item in (*self.invocation.inputs,*report.result.outcome.outputs)]
        references.extend(item for item in (self.invocation.checkpoint,report.result.outcome.checkpoint) if item is not None)
        if any(item.scope != report.scope for item in references):
            raise ProducerProofError('producer_source_scope_inconsistent')

    def to_wire(self):
        return AcceptedToolExecution(wire_version='1',authority='accepted_execution',worker_id=self.worker_id,
            invocation=self.invocation,completion=self.completion)
