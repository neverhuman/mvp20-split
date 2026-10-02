"""Exact command identity and receipt-first bounded recovery."""

import json
from dataclasses import dataclass

from amphora_contracts_artifacts import DerivedUploadObservation, PublicationObservation
from amphora_contracts_commands import CanonicalCommand, CommandIdentity
from amphora_contracts_core import Scope
from amphora_contracts_runtime import ClaimResponse, CommandReceipt
from pydantic import TypeAdapter, ValidationError

from .transport import ProtocolError, TransportLost

RUNTIME_RECEIPT = TypeAdapter(ClaimResponse | CommandReceipt)


class CommandRejected(ProtocolError):
    def __init__(self, reason_code):
        self.reason_code = reason_code
        super().__init__(reason_code)


class CommandUnresolved(ProtocolError):
    def __init__(self, command):
        self.identity = command.identity
        self.request_sha256 = command.sha256
        super().__init__("command_unresolved")


@dataclass(frozen=True, slots=True)
class WorkerIdentity:
    actor_id: str
    scope: Scope

    def command(self, family, key, payload):
        identity = CommandIdentity(command_family=family, command_id=key, actor_id=self.actor_id, scope=self.scope)
        return CanonicalCommand.for_family(json.dumps({"identity": identity.model_dump(mode="json"),
            "payload": payload.model_dump(mode="json")}), family, type(payload))


def decoded(model, payload):
    try:
        return model.validate_json(payload) if isinstance(model, TypeAdapter) else model.model_validate_json(payload)
    except (ValidationError, ValueError) as error:
        raise ProtocolError("invalid_owner_response") from error


def verify_binding(command, identity, digest):
    if identity != command.identity or digest != command.sha256:
        raise ProtocolError("receipt_binding_mismatch")


def runtime_result(command, payload):
    result = decoded(RUNTIME_RECEIPT, payload)
    binding = result.outcome.receipt.binding if isinstance(result, ClaimResponse) else result.outcome.binding
    verify_binding(command, binding.identity, binding.request_sha256)
    if result.outcome.status == "rejected":
        raise CommandRejected(result.outcome.reason_code)
    return result


def publication_result(command, payload):
    result = decoded(PublicationObservation, payload)
    verify_binding(command, result.identity, result.request_sha256)
    if result.outcome.status == "rejected":
        raise CommandRejected(result.outcome.reason_code)
    return result


def derived_publication_result(command, payload):
    result = decoded(DerivedUploadObservation, payload)
    verify_binding(command, result.identity, result.request_sha256)
    if result.outcome.status == "rejected":
        raise CommandRejected(result.outcome.reason_code)
    return result


class CommandExchange:
    """Retries preserve bytes/key; after ambiguity, inspect before every resubmit."""

    def __init__(self, transport):
        self.transport = transport

    def execute(self, command, path, direct, recovered, *, guard=lambda: None, resume=False):
        receipt_path = f"/v1/commands/{command.identity.command_family}/{command.identity.command_id}"
        inspect_first = resume
        for _ in range(3):
            if inspect_first:
                try:
                    reply = self.transport.request("GET", receipt_path)
                except TransportLost:
                    continue
                if reply.status == 200:
                    result = recovered(command, reply.body)
                    if result.outcome.status != "pending":
                        return result
                elif reply.status != 404:
                    if reply.status in {408, 429} or reply.status >= 500:
                        continue
                    raise ProtocolError("receipt_lookup_denied")
            guard()
            try:
                reply = self.transport.request("POST", path, command.canonical_bytes)
            except TransportLost:
                inspect_first = True
                continue
            if reply.status == 200:
                result = direct(command, reply.body)
                if getattr(result, "outcome", None) is None or result.outcome.status != "pending":
                    return result
            elif reply.status not in {408, 429} and reply.status < 500:
                # Domain publication errors persist original rejections; inspect even 409.
                if reply.status in {401, 403, 404, 422}:
                    raise ProtocolError("command_request_denied")
            inspect_first = True
        raise CommandUnresolved(command)
