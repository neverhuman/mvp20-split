"""Notifications request an authoritative refresh; they never grant execution authority."""

from typing import Literal

from amphora_contracts_core import Identifier, Scope, WireModel

from .models import Revision


class NotificationReference(WireModel):
    kind: Literal["run", "worker_policy"]
    object_id: Identifier
    revision: Revision


class RuntimeNotification(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    operation_id: Identifier
    event_id: Identifier
    event_kind: Identifier
    reference: NotificationReference


class DeliveryAcknowledgement(WireModel):
    schema_version: Literal["1"] = "1"
    scope: Scope
    operation_id: Identifier
    event_id: Identifier
    status: Literal["acknowledged"]
