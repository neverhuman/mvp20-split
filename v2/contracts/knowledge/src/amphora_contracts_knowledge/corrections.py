"""Reference-only Knowledge correction and explicit future-campaign selection."""
from typing import Literal

from amphora_contracts_core import Identifier, WireModel
from amphora_contracts_graph_runtime import ReceiptChainRef, ReceiptRevisionRef

from .publication import ReasoningPublicationRequest


class CorrectReasoningReceipt(WireModel):
    wire_version: Literal["1"]
    chain: ReceiptChainRef
    change_id: Identifier
    source: ReasoningPublicationRequest
    reason_code: Identifier
    expected_head: ReceiptRevisionRef | None


class SelectReasoningReceipt(WireModel):
    wire_version: Literal["1"]
    chain: ReceiptChainRef
    revision: ReceiptRevisionRef | None
