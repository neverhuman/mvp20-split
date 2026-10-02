"""Public wire models and closed family parsing; no state or authority policy."""

import json

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError

from .derivations import (
    BeginDerivedUpload,
    DerivationDeclaration,
    DerivationReceipt,
    DerivedUploadAccepted,
    DerivedUploadObservation,
    DerivedUploadReceipt,
    TransformationDescriptor,
)
from .models import (
    BeginUpload,
    CompletionIntentBinding,
    ConfirmRetention,
    ContentDescriptor,
    FinalizationAccepted,
    FinalizeArtifact,
    FinalizedReceipt,
    PublicationObservation,
    PublicationPending,
    PublicationRejected,
    ReconcileReservation,
    ReservationBinding,
    ReservationReceipt,
    ReserveArtifact,
    RuntimeOutcome,
    UploadAccepted,
    UploadContentReceipt,
    UploadReceipt,
)

OPERATIONS = {
    "artifacts.begin_derived_upload": BeginDerivedUpload,
    "artifacts.begin_upload": BeginUpload,
    "artifacts.finalize": FinalizeArtifact,
    "artifacts.reserve": ReserveArtifact,
    "artifacts.confirm": ConfirmRetention,
    "artifacts.reconcile": ReconcileReservation,
}


def parse_command(family: str, raw: str | bytes) -> CanonicalCommand:
    try:
        model = OPERATIONS[family]
    except KeyError as error:
        raise CommandEncodingError("unknown_family") from error
    command = CanonicalCommand.for_family(raw, family, model)
    payload = json.loads(command.canonical_bytes)["payload"]
    expected_scope = command.identity.scope.model_dump()
    for artifact in _references(family, payload):
        if artifact["scope"] != expected_scope:
            raise CommandEncodingError("scope_mismatch")
    return command



__all__ = ['BeginUpload', 'CompletionIntentBinding', 'ConfirmRetention', 'ContentDescriptor', 'FinalizeArtifact', 'FinalizedReceipt', 'ReconcileReservation', 'ReservationBinding', 'ReservationReceipt', 'ReserveArtifact', 'RuntimeOutcome', 'UploadContentReceipt', 'UploadReceipt', 'parse_command']
__all__ += ['PublicationObservation', 'PublicationPending', 'PublicationRejected', 'UploadAccepted', 'FinalizationAccepted']
__all__ += ['BeginDerivedUpload', 'DerivationDeclaration', 'DerivationReceipt', 'DerivedUploadAccepted',
            'DerivedUploadObservation', 'DerivedUploadReceipt', 'TransformationDescriptor']


def _references(family, payload):
    if family == "artifacts.begin_derived_upload":
        yield from payload["declaration"]["inputs"]
    if family == "artifacts.reserve":
        yield payload["artifact"]
