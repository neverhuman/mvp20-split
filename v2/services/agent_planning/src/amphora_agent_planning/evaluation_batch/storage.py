"""Append-only suite registration; physical attempts stay in the existing owner ledger."""

import json

from sqlalchemy import text

from ..budget import BudgetPolicy
from ..context import RequestSnapshot
from ..context.policy import require
from ..evaluation import EvaluationProtocol
from ..evaluation.protocol import canonical, document
from .binding import EvaluationBatch

KEY = 'tenant_id=:tenant AND project_id=:project AND suite_id=:suite'


class EvaluationJournal:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _params(principal, suite_id):
        return {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
                'suite': suite_id, 'actor': principal.actor_id}

    @staticmethod
    def _inputs(batch):
        inputs = {}
        for task in batch.tasks:
            value = {'request': json.loads(task.original.canonical), 'policy': json.loads(task.policy.canonical)}
            previous = inputs.setdefault(task.case_id, value)
            require(previous == value, 'evaluation_case_input_conflict')
        return canonical(inputs)

    @staticmethod
    def _decode(principal, manifest, corpus, inputs):
        protocol = EvaluationProtocol.load(manifest, corpus)
        decoded = document(inputs, limit=16777216)
        require(isinstance(decoded, dict), 'evaluation_stored_inputs')
        requests, policies = {}, {}
        for case_id, value in decoded.items():
            require(isinstance(value, dict) and set(value) == {'request', 'policy'}, 'evaluation_stored_input')
            requests[case_id] = RequestSnapshot.from_bytes(canonical(value['request']),
                actor_id=principal.actor_id, scope=principal.scope)
            policies[case_id] = BudgetPolicy.from_bytes(canonical(value['policy']))
        # Caller authorizes reads/writes; pure reconstruction never manufactures a grant.
        return protocol, EvaluationBatch._bind(protocol, principal, requests, policies)

    @classmethod
    def _read(cls, conn, principal, params):
        row = conn.execute(text('SELECT * FROM planning.evaluation_suites WHERE ' + KEY), params).mappings().first()
        if row is None:
            return None
        require(row['actor_id'] == principal.actor_id, 'evaluation_actor_mismatch')
        protocol, batch = cls._decode(principal, bytes(row['manifest_bytes']), bytes(row['corpus_bytes']), bytes(row['input_bytes']))
        require(protocol.sha256 == row['protocol_sha256'] and batch.sha256 == row['batch_sha256'] and
                protocol.manifest.suite_id == row['suite_id'], 'evaluation_stored_identity')
        return protocol, batch

    def read(self, principal, suite_id):
        principal.require('read_attempts', principal.scope)
        with self.engine.connect() as conn:
            return self._read(conn, principal, self._params(principal, suite_id))

    def register(self, principal, protocol, batch):
        principal.require('record_requests', principal.scope)
        manifest = canonical(protocol.manifest.model_dump(mode='json'))
        inputs = self._inputs(batch)
        checked_protocol, checked_batch = self._decode(principal, manifest, protocol.corpus_bytes, inputs)
        require(checked_protocol.sha256 == protocol.sha256 and checked_batch == batch, 'evaluation_batch_conflict')
        params = self._params(principal, protocol.manifest.suite_id)
        with self.engine.begin() as conn:
            token = json.dumps(['planning.evaluation.v1', params['tenant'], params['project'], params['suite']])
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'), {'token': token})
            existing = self._read(conn, principal, params)
            if existing is not None:
                require(existing == (checked_protocol, checked_batch), 'evaluation_suite_conflict')
                return existing
            conn.execute(text('INSERT INTO planning.evaluation_suites '
                '(tenant_id,project_id,suite_id,actor_id,protocol_sha256,batch_sha256,manifest_bytes,corpus_bytes,input_bytes) '
                'VALUES (:tenant,:project,:suite,:actor,:protocol,:batch,:manifest,:corpus,:inputs)'),
                {**params, 'protocol': protocol.sha256, 'batch': batch.sha256,
                 'manifest': manifest, 'corpus': protocol.corpus_bytes, 'inputs': inputs})
        return checked_protocol, checked_batch
