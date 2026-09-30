"""Explicit next-campaign admission pins; retained compilation is not an execution grant."""

from amphora_contracts_core import Digest, Identifier, SafePositiveInt, WireModel

from .models import AdmitGraphRun


class DraftSelection(WireModel):
    draft_id: Identifier
    revision: SafePositiveInt
    content_sha256: Digest
    validation_id: Identifier
    universe_sha256: Digest


class AdmitDraft(AdmitGraphRun):
    draft: DraftSelection
