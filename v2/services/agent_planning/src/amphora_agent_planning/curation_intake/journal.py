"""Atomic original intent and receipt; no model call or peer transaction."""
import hashlib

from amphora_contracts_campaign_curation import CurationReceiptQuery
from sqlalchemy import text

from ..context.policy import require
from .commands import CurationCommand
from .record import OriginalCuration, encoded

KEY = 'tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND command_id=:command'


class CurationJournal:
    def __init__(self, engine, policy_ids):
        self.engine = engine
        self.policy_ids = frozenset(policy_ids)

    @staticmethod
    def _key(identity):
        return {'tenant': identity.scope.tenant_id, 'project': identity.scope.project_id,
                'actor': identity.actor_id, 'command': identity.command_id}

    def receive(self, principal, raw):
        # Recover an existing original even if its policy has since been retired.
        incoming = CurationCommand.restore(raw)
        principal.require('record_curations', incoming.command.identity.scope)
        if principal.actor_id != incoming.command.identity.actor_id:
            raise PermissionError('planning_access_denied')
        key = self._key(incoming.command.identity)
        with self.engine.begin() as conn:
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'),
                         {'token': incoming.curation_id})
            row = conn.execute(text('SELECT * FROM planning.curation_requests WHERE ' + KEY), key).mappings().one_or_none()
            if row is not None:
                original = OriginalCuration.restore(row)
                incoming.reconcile(original.incoming.command.canonical_bytes)
                return original.receipt
            admitted = CurationCommand.bind(principal, raw, self.policy_ids)
            record = OriginalCuration(admitted, conn.execute(text('SELECT clock_timestamp()')).scalar_one())
            self._insert(conn, key, record)
            return record.receipt

    @staticmethod
    def _insert(conn, key, record):
        command = record.incoming.command
        receipt = encoded(record.receipt)
        conn.execute(text('INSERT INTO planning.curation_requests '
            '(tenant_id,project_id,actor_id,command_id,curation_id,command_sha256,command_bytes,'
            'receipt_sha256,receipt_bytes,recorded_at) VALUES '
            '(:tenant,:project,:actor,:command,:curation,:digest,:canonical,:receipt_digest,:receipt,:at)'),
            {**key, 'curation': record.incoming.curation_id, 'digest': command.sha256,
             'canonical': command.canonical_bytes, 'receipt_digest': hashlib.sha256(receipt).hexdigest(),
             'receipt': receipt, 'at': record.recorded_at})

    def receipt(self, principal, query: CurationReceiptQuery):
        principal.require('read_curations', query.identity.scope)
        if principal.actor_id != query.identity.actor_id:
            raise PermissionError('planning_access_denied')
        require(query.identity.command_family == 'planning.curate_campaign', 'curation_query_family')
        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT * FROM planning.curation_requests WHERE ' + KEY),
                               self._key(query.identity)).mappings().one_or_none()
        if row is None:
            return None
        original = OriginalCuration.restore(row)
        original.incoming.require_read(principal)
        require(original.receipt.identity == query.identity
                and original.receipt.request_sha256 == query.request_sha256, 'curation_receipt_conflict')
        return original.receipt

    def read(self, principal, curation_id):
        principal.require('read_curations', principal.scope)
        with self.engine.connect() as conn:
            row = conn.execute(text('SELECT * FROM planning.curation_requests WHERE '
                'tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND curation_id=:curation'),
                {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
                 'actor': principal.actor_id, 'curation': curation_id}).mappings().one_or_none()
            if row is None:
                return None
            original = OriginalCuration.restore(row)
            original.incoming.require_read(principal)
            from ..curation_jobs.journal import current
            from ..capability_requests.projection import CurationCapabilities
            progress = current(conn, original)
            return CurationCapabilities.enrich(progress.view if progress is not None else original.view())
