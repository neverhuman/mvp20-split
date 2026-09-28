"""Configured delivery endpoints and exact typed acknowledgements."""

import json

from amphora_contracts_artifacts import ReservationBinding, ReservationReceipt, parse_command
from amphora_contracts_runtime import DeliveryAcknowledgement

from ..completion.artifacts import ArtifactReservations


class DeliveryUnavailable(Exception):
    pass


def exchange(client, endpoint, raw):
    from urllib.error import URLError
    from urllib.request import Request
    request = Request(endpoint, data=raw, method="POST", headers={
        "Authorization": "Bearer " + client.token, "Content-Type": "application/json"})
    try:
        with client.opener.open(request, timeout=client.timeout) as response:
            data = response.read(262145)
            if len(data) > 262144:
                raise DeliveryUnavailable("delivery_response_too_large")
            return data
    except (URLError, OSError, ValueError) as error:
        raise DeliveryUnavailable("delivery_unavailable") from error


class NotificationSink:
    def __init__(self, endpoint, token, *, timeout=5):
        # Same owner-local HTTPS/loopback, no redirect/proxy and bounded timeout policy.
        self.client = ArtifactReservations("runtime_notifications", endpoint, token, timeout=timeout)

    def send(self, claim):
        notification = claim.notification()
        raw = exchange(self.client, self.client.endpoint, notification.model_dump_json().encode())
        try:
            ack = DeliveryAcknowledgement.model_validate_json(raw)
        except ValueError as error:
            raise DeliveryUnavailable("invalid_delivery_ack") from error
        if (ack.scope, ack.operation_id, ack.event_id) != (claim.scope, claim.operation_id, claim.event_id):
            raise DeliveryUnavailable("delivery_ack_mismatch")


class DeliveryTargets:
    def __init__(self, artifacts=None, notifications=None):
        self.artifacts = artifacts
        self.notifications = dict(notifications or {})
        if self.notifications.keys() - {"runtime_notifications", "runtime_policy_notifications"}:
            raise ValueError("Unknown notification target")

    def send(self, claim):
        if claim.target in self.notifications:
            return self.notifications[claim.target].send(claim)
        if claim.target not in {"artifact_confirm", "artifact_reconcile"} or self.artifacts is None:
            raise DeliveryUnavailable("delivery_target_unavailable")
        kind = claim.target.removeprefix("artifact_")
        command = parse_command("artifacts." + kind, json.dumps(claim.payload["command"]))
        expected = ReservationBinding.model_validate_json(json.dumps(claim.payload["binding"]))
        if (command.identity.actor_id != self.artifacts.owner or command.identity.scope != claim.scope or
            expected.artifact.scope != claim.scope or expected.intent.runtime_owner != self.artifacts.owner):
            raise DeliveryUnavailable("delivery_binding_mismatch")
        raw = exchange(self.artifacts, self.artifacts.endpoint.rstrip("/") + "/" + kind, command.canonical_bytes)
        try:
            receipt = ReservationReceipt.model_validate_json(raw)
        except ValueError as error:
            raise DeliveryUnavailable("invalid_retention_ack") from error
        if receipt.outcome.binding != expected:
            raise DeliveryUnavailable("retention_ack_mismatch")
        if kind == "confirm":
            if (receipt.outcome.status != "confirmed" or receipt.outcome.proof.runtime_receipt_id !=
                claim.payload["command"]["payload"]["runtime_receipt_id"]):
                raise DeliveryUnavailable("retention_ack_mismatch")
        elif receipt.outcome.status != "released":
            raise DeliveryUnavailable("retention_ack_mismatch")
