"""Public wire models and closed family parsing; no state or authority policy."""

import json

from amphora_contracts_commands import CanonicalCommand, CommandEncodingError

from .delivery import DeliveryAcknowledgement, RuntimeNotification
from .inspection import AuditPage, CompletionRecord, DeliveryPage
from .models import (
    AdmitFixtureRun,
    AttemptBudget,
    AttemptRef,
    CancelRun,
    ClaimInvocation,
    ClaimResponse,
    CommandReceipt,
    CompleteInvocation,
    PreparedInvocation,
    RenewAttempt,
    RevokeWorker,
)
from .views import RunSnapshot

OPERATIONS = {
    "runtime.admit_fixture": AdmitFixtureRun,
    "runtime.claim": ClaimInvocation,
    "runtime.renew": RenewAttempt,
    "runtime.complete": CompleteInvocation,
    "runtime.cancel": CancelRun,
    "runtime.revoke_worker": RevokeWorker,
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



__all__ = ['AdmitFixtureRun', 'AttemptBudget', 'AttemptRef', 'CancelRun', 'ClaimInvocation', 'ClaimResponse', 'CommandReceipt', 'CompleteInvocation', 'PreparedInvocation', 'RenewAttempt', 'RevokeWorker', 'RunSnapshot', 'RuntimeNotification', 'DeliveryAcknowledgement', 'AuditPage', 'CompletionRecord', 'DeliveryPage', 'parse_command']


def _references(family, payload):
    if family == "runtime.admit_fixture":
        for invocation in payload["invocations"]:
            yield from (item["artifact"] for item in invocation["inputs"])
            if invocation["checkpoint"] is not None:
                yield invocation["checkpoint"]
    elif family == "runtime.complete":
        outcome = payload["completion"]["outcome"]
        if outcome["status"] == "succeeded":
            yield from (item["artifact"] for item in outcome["outputs"])
            if outcome["checkpoint"] is not None:
                yield outcome["checkpoint"]
