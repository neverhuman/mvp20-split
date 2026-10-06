"""Historical accepted execution evidence, never a live grant or scientific verdict."""
from typing import Literal

from amphora_contracts_core import Identifier, WireModel
from amphora_contracts_runtime import CompletionRecord, PreparedInvocation


class AcceptedToolExecution(WireModel):
    wire_version: Literal["1"]
    authority: Literal["accepted_execution"]
    worker_id: Identifier
    invocation: PreparedInvocation
    completion: CompletionRecord


__all__ = ["AcceptedToolExecution"]
