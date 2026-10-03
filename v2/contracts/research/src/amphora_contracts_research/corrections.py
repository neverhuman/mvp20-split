"""Explicit owner-source correction and future-campaign selection requests."""
from typing import Literal

from amphora_contracts_core import Identifier, WireModel
from amphora_contracts_graph_runtime import ReceiptChainRef, ReceiptRevisionRef


class CorrectAssessmentReceipt(WireModel):
    wire_version: Literal["1"]
    chain: ReceiptChainRef
    change_id: Identifier
    assessment_id: Identifier
    reason_code: Identifier
    expected_head: ReceiptRevisionRef | None


class SelectAssessmentReceipt(WireModel):
    wire_version: Literal["1"]
    chain: ReceiptChainRef
    revision: ReceiptRevisionRef | None
