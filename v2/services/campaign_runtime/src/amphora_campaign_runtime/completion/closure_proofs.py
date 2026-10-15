"""Runtime-private immutable proof companion; root receipt/outbox remain unchanged."""

import json

from amphora_contracts_artifact_retention import DerivedClosureReservationReceipt
from sqlalchemy import text

from ..lifecycle.claims import SCOPE
from .artifacts import ReservationUnavailable, validate_receipt


def validate(reservation, root, body):
    try:
        proof = DerivedClosureReservationReceipt.model_validate_json(json.dumps(body))
        validate_receipt(reservation, proof.reservation)
    except (ValueError, ReservationUnavailable) as error:
        raise ReservationUnavailable("artifact_closure_binding_mismatch") from error
    if proof.reservation != root:
        raise ReservationUnavailable("artifact_closure_binding_mismatch")
    return proof


def load(conn, params):
    return conn.execute(text("SELECT receipt FROM runtime.intent_retention_closures WHERE " + SCOPE +
        " AND intent_id=:intent AND output_binding=:output"), params).scalar_one_or_none()


def store(conn, params, proof):
    conn.execute(text("INSERT INTO runtime.intent_retention_closures "
        "(tenant_id,project_id,intent_id,output_binding,receipt) VALUES "
        "(:tenant,:project,:intent,:output,CAST(:proof AS jsonb)) ON CONFLICT DO NOTHING"),
        {**params, "proof": proof.model_dump_json()})
    if load(conn, params) != proof.model_dump(mode="json"):
        raise ReservationUnavailable("artifact_closure_receipt_conflict")
