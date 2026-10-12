"""One immutable terminal verification per original; first verified gap wins."""
from dataclasses import dataclass
import hashlib
from datetime import UTC

from amphora_contracts_campaign_curation import CapabilityFulfillmentReceipt
from sqlalchemy import text

from ..context.policy import require
from ..curation_intake.record import encoded
from .original import OriginalFulfillment
from .witness import VerificationWitness
from .failures import rejection


@dataclass(frozen=True)
class VerificationResult:
    receipt: CapabilityFulfillmentReceipt
    witness: VerificationWitness | None

    @classmethod
    def create(cls, original, status, reason, at, witness=None):
        require(status in {'verified', 'rejected'} and at.utcoffset() is not None
            and at >= original.recorded_at, 'fulfillment_verification_state')
        require((status == 'verified' and reason is None and witness is not None)
            or (status == 'rejected' and reason is not None), 'fulfillment_verification_reason')
        if witness is not None:
            witness.validate(original)
        receipt = CapabilityFulfillmentReceipt.model_validate_json(original.receipt.model_copy(update={
            'status': status, 'reason_code': reason, 'created_at': at.astimezone(UTC)}).model_dump_json())
        return cls(receipt, witness)

    @classmethod
    def restore(cls, original, row):
        raw = bytes(row['receipt_bytes'])
        receipt = CapabilityFulfillmentReceipt.model_validate_json(raw)
        witness_raw = row['witness_bytes']
        witness = None if witness_raw is None else VerificationWitness(bytes(witness_raw))
        result = cls.create(original, receipt.status, receipt.reason_code, receipt.created_at, witness)
        require(result.receipt == receipt and encoded(receipt) == raw
            and hashlib.sha256(raw).hexdigest() == row['receipt_sha256']
            and receipt.status == row['status'] and receipt.created_at == row['recorded_at']
            and row['request_id'] == original.capability.reference.request_id
            and row['fulfillment_id'] == original.incoming.fulfillment_id
            and row['tenant_id'] == receipt.identity.scope.tenant_id
            and row['project_id'] == receipt.identity.scope.project_id
            and row['actor_id'] == receipt.identity.actor_id, 'stored_fulfillment_verification_mismatch')
        require((witness is None and row['witness_sha256'] is None)
            or (witness is not None and hashlib.sha256(witness.canonical).hexdigest() == row['witness_sha256']),
            'stored_fulfillment_witness_mismatch')
        return result


def lookup(conn, original):
    identity = original.incoming.command.identity
    row = conn.execute(text('SELECT * FROM planning.capability_verifications WHERE '
        'tenant_id=:tenant AND project_id=:project AND fulfillment_id=:fulfillment'),
        {'tenant': identity.scope.tenant_id, 'project': identity.scope.project_id,
         'fulfillment': original.incoming.fulfillment_id}).mappings().one_or_none()
    return None if row is None else VerificationResult.restore(original, row)


class FulfillmentVerifier:
    def __init__(self, engine, collector):
        self.engine, self.collector = engine, collector

    def verify(self, principal, fulfillment_id):
        principal.require('execute_curations', principal.scope)
        key = {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
               'actor': principal.actor_id, 'fulfillment': fulfillment_id}
        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT * FROM planning.capability_fulfillments WHERE '
                'tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND fulfillment_id=:fulfillment'),
                key).mappings().one_or_none()
            require(row is not None, 'fulfillment_original_not_found')
            original = OriginalFulfillment.restore(row)
            original.require_worker(principal)
            prior = lookup(conn, original)
            if prior is not None:
                return prior.receipt
        # No SQL connection/transaction spans peer reads; retries are read-only.
        witness, status, reason = None, 'verified', None
        try:
            review = self.collector.collect(original.capability, original.incoming.request.payload)
            witness = VerificationWitness.capture(original, review)
        except ValueError as error:
            reason = rejection(error)
            if reason is None:
                raise
            status = 'rejected'
        return self._commit(original, key, status, reason, witness)

    def _commit(self, original, key, status, reason, witness):
        request_id = original.capability.reference.request_id
        with self.engine.begin() as conn:
            # Same request lock covers competing commands and retries of one command.
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'),
                {'token': 'capability-verification:' + key['tenant'] + ':' + key['project'] + ':' + request_id})
            prior = lookup(conn, original)
            if prior is not None:
                return prior.receipt
            winner = conn.execute(text('SELECT fulfillment_id FROM planning.capability_verifications WHERE '
                'tenant_id=:tenant AND project_id=:project AND request_id=:request AND status=\'verified\''),
                {**key, 'request': request_id}).scalar_one_or_none()
            if winner is not None:
                status, reason = 'rejected', 'capability_already_fulfilled'
            result = VerificationResult.create(original, status, reason,
                conn.execute(text('SELECT clock_timestamp()')).scalar_one(), witness)
            self._insert(conn, key, request_id, result)
            return result.receipt

    @staticmethod
    def _insert(conn, key, request_id, result):
        raw = encoded(result.receipt)
        witness = None if result.witness is None else result.witness.canonical
        conn.execute(text('INSERT INTO planning.capability_verifications '
            '(tenant_id,project_id,actor_id,fulfillment_id,request_id,status,receipt_bytes,receipt_sha256,'
            'witness_bytes,witness_sha256,recorded_at) VALUES '
            '(:tenant,:project,:actor,:fulfillment,:request,:status,:receipt,:digest,:witness,:witness_digest,:at)'),
            {**key, 'request': request_id, 'status': result.receipt.status, 'receipt': raw,
             'digest': hashlib.sha256(raw).hexdigest(), 'witness': witness,
             'witness_digest': None if witness is None else hashlib.sha256(witness).hexdigest(),
             'at': result.receipt.created_at})
