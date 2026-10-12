"""Own append-only intake; no peer calls or verification during admission."""
import hashlib
from sqlalchemy import text

from ..capability_requests.reader import load_original
from ..context.policy import require
from ..curation_intake.commands import FulfillmentCommand
from ..curation_intake.record import encoded
from .original import OriginalFulfillment

KEY = 'tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND command_id=:command'


def command_key(identity):
    return {'tenant': identity.scope.tenant_id, 'project': identity.scope.project_id,
            'actor': identity.actor_id, 'command': identity.command_id}


class FulfillmentJournal:
    def __init__(self, engine):
        self.engine = engine

    def receive(self, principal, raw):
        incoming = FulfillmentCommand.bind(principal, raw)
        key = command_key(incoming.command.identity)
        with self.engine.begin() as conn:
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'),
                         {'token': incoming.fulfillment_id})
            row = conn.execute(text('SELECT * FROM planning.capability_fulfillments WHERE ' + KEY),
                               key).mappings().one_or_none()
            if row is not None:
                original = OriginalFulfillment.restore(row)
                incoming.reconcile(original.incoming.command.canonical_bytes)
                return original.receipt
            capability = load_original(conn, principal, incoming.request.payload.request.request_id)
            require(capability is not None, 'capability_request_not_found')
            original = OriginalFulfillment(incoming, capability,
                conn.execute(text('SELECT clock_timestamp()')).scalar_one())
            self._insert(conn, key, original)
            return original.receipt

    @staticmethod
    def _insert(conn, key, original):
        command = original.incoming.command
        receipt, capability = encoded(original.receipt), encoded(original.capability.view())
        conn.execute(text('INSERT INTO planning.capability_fulfillments '
            '(tenant_id,project_id,actor_id,command_id,fulfillment_id,request_id,command_sha256,command_bytes,'
            'capability_sha256,capability_bytes,receipt_sha256,receipt_bytes,recorded_at) VALUES '
            '(:tenant,:project,:actor,:command,:fulfillment,:request,:digest,:canonical,'
            ':capability_digest,:capability,:receipt_digest,:receipt,:at)'),
            {**key, 'fulfillment': original.incoming.fulfillment_id,
             'request': original.capability.reference.request_id, 'digest': command.sha256,
             'canonical': command.canonical_bytes, 'capability': capability,
             'capability_digest': hashlib.sha256(capability).hexdigest(), 'receipt': receipt,
             'receipt_digest': hashlib.sha256(receipt).hexdigest(), 'at': original.recorded_at})
