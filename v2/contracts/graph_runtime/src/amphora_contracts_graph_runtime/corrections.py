"""Immutable owner correction records; selection and authority remain owner behavior."""

from typing import Literal

from amphora_contracts_core import Digest, Identifier, SafePositiveInt, Scope, WireModel

from .waits import DomainReceipt


class ReceiptChainRef(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    issuer_id: Identifier
    chain_id: Identifier


class ReceiptRevisionRef(WireModel):
    schema_version: Literal["1"] = "1"
    chain: ReceiptChainRef
    ordinal: SafePositiveInt
    record_sha256: Digest


class ReceiptCorrection(WireModel):
    schema_version: Literal["1"] = "1"
    chain: ReceiptChainRef
    ordinal: SafePositiveInt
    change_id: Identifier
    actor_id: Identifier
    reason_code: Identifier
    source_receipt: DomainReceipt
    predecessor: ReceiptRevisionRef | None
    receipt: DomainReceipt
    notice: DomainReceipt | None


class ReceiptCorrectionView(WireModel):
    schema_version: Literal["1"] = "1"
    reference: ReceiptRevisionRef
    record: ReceiptCorrection
