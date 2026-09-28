"""Immutable runtime outcome proof and durable terminal artifact delivery intents."""

import json
import uuid

from amphora_contracts_artifacts import ReservationReceipt, RuntimeOutcome, parse_command
from sqlalchemy import text

from ..lifecycle.claims import RUN, SCOPE
from ..lifecycle.model import TransitionError


def matches(intent, binding):
    expected = {"artifact": binding.artifact.model_dump(mode="json"), "intent": binding.intent.model_dump(mode="json")}
    return expected in intent["output_bindings"] and intent["semantic_sha256"] == binding.intent.semantic_completion_sha256


def queue_terminal(conn, params, intent_ids):
    """Caller holds run/work/intent locks and has appended the transition audit."""
    queued = []
    for intent_id in intent_ids:
        values = {**params, "intent": intent_id}
        intent = conn.execute(text("SELECT * FROM runtime.completion_intents WHERE " + RUN +
            " AND intent_id=:intent"), values).mappings().one()
        if intent["status"] not in {"committed", "aborted"}:
            continue
        rows = conn.execute(text("SELECT receipt FROM runtime.intent_reservations WHERE " + SCOPE +
            " AND intent_id=:intent ORDER BY output_binding"), values).scalars().all()
        for raw in rows:
            try:
                binding = ReservationReceipt.model_validate_json(json.dumps(raw)).outcome.binding
            except ValueError:
                continue  # Invalid stored evidence cannot authorize a remote operation.
            if not matches(intent, binding):
                continue
            kind = "confirm" if intent["status"] == "committed" else "reconcile"
            operation = uuid.uuid5(uuid.NAMESPACE_URL, json.dumps([
                "amphora-retention-v1", binding.artifact.scope.model_dump(), intent_id,
                binding.intent.output_binding, kind], sort_keys=True)).hex
            payload = {"reservation_id": binding.reservation_id}
            if kind == "confirm":
                payload.update(intent_id=intent_id, runtime_receipt_id=intent["outcome"]["runtime_receipt_id"])
            command = parse_command("artifacts." + kind, json.dumps({"identity": {
                "command_family": "artifacts." + kind, "command_id": operation,
                "actor_id": binding.intent.runtime_owner, "scope": binding.artifact.scope.model_dump()}, "payload": payload}))
            event = conn.execute(text("SELECT event_id FROM runtime.audit_events WHERE " + RUN +
                " ORDER BY revision DESC,ordinal DESC LIMIT 1"), values).scalar_one()
            conn.execute(text("INSERT INTO runtime.outbox (operation_id,event_id,target,payload) "
                "VALUES (:operation,:event,:target,CAST(:payload AS jsonb)) ON CONFLICT DO NOTHING"),
                {"operation": operation, "event": event, "target": "artifact_" + kind,
                 "payload": json.dumps({"command": json.loads(command.canonical_bytes),
                                        "binding": binding.model_dump(mode="json")})})
            queued.append(operation)
    return tuple(queued)


class IntentOutcomes:
    def __init__(self, engine, runtime_owner):
        self.engine, self.runtime_owner = engine, runtime_owner

    def lookup(self, principal, binding):
        principal.require("outcome")
        if binding.artifact.scope != principal.scope:
            raise TransitionError("access_denied")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id,
                  "intent": binding.intent.intent_id, "output": binding.intent.output_binding}
        proof = {"status": "unknown"}
        if binding.intent.runtime_owner == self.runtime_owner:
            with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn, conn.begin():
                conn.execute(text("SET TRANSACTION READ ONLY"))
                intent = conn.execute(text("SELECT * FROM runtime.completion_intents WHERE " + SCOPE +
                    " AND intent_id=:intent"), params).mappings().one_or_none()
                if intent is not None and matches(intent, binding):
                    if intent["status"] == "prepared":
                        proof = {"status": "prepared"}
                    elif intent["status"] == "aborted":
                        # Lost reserve responses may leave no saved reservation ID. The exact semantic
                        # binding is still permanently aborted and authorizes its owner's release.
                        proof = intent["outcome"]
                    else:
                        raw = conn.execute(text("SELECT receipt FROM runtime.intent_reservations WHERE " + SCOPE +
                            " AND intent_id=:intent AND output_binding=:output"), params).scalar_one_or_none()
                        if raw is not None and ReservationReceipt.model_validate_json(json.dumps(raw)).outcome.binding == binding:
                            proof = intent["outcome"]
        return RuntimeOutcome.model_validate({"binding": binding, "proof": proof})
