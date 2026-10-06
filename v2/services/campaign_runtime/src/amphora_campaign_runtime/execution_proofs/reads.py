"""One scoped read-only owner join; neither a caller report nor a historical lease grants authority."""
import json

from amphora_contracts_runtime import CompletionRecord, PreparedInvocation
from sqlalchemy import text

from ..inspection.cursors import InspectionError
from .projection import ProducerProofError, ProducerSnapshot


class ExecutionProofs:
    def __init__(self, engine):
        self.engine = engine

    def read(self, principal, run_id, completion_id):
        principal.require('read')
        principal.require('inspect_receipts')
        parameters = {'tenant':principal.scope.tenant_id,'project':principal.scope.project_id,'run':run_id,'completion':completion_id}
        with self.engine.connect().execution_options(isolation_level='REPEATABLE READ') as connection, connection.begin():
            connection.execute(text('SET TRANSACTION READ ONLY'))
            row = connection.execute(text('''SELECT r.*, a.specification, t.worker_id, c.receipt
                FROM runtime.attempt_reports r
                JOIN runtime.accepted_completions accepted
                  ON (accepted.tenant_id,accepted.project_id,accepted.completion_id)=(r.tenant_id,r.project_id,r.report_id)
                JOIN runtime.activations a
                  ON (a.tenant_id,a.project_id,a.run_id,a.activation_id)=(r.tenant_id,r.project_id,r.run_id,r.activation_id)
                JOIN runtime.attempts t
                  ON (t.tenant_id,t.project_id,t.run_id,t.activation_id,t.attempt_id,t.fence)=
                     (r.tenant_id,r.project_id,r.run_id,r.activation_id,r.attempt_id,r.fence)
                JOIN runtime.commands c
                  ON (c.tenant_id,c.project_id,c.operation_id)=(r.tenant_id,r.project_id,r.report_id)
                WHERE r.tenant_id=:tenant AND r.project_id=:project AND r.run_id=:run AND r.report_id=:completion
                  AND t.settled AND t.status='succeeded' ''') ,parameters).mappings().one_or_none()
            if row is None:
                raise InspectionError('producer_unavailable')
            try:
                completion = CompletionRecord.model_validate_json(json.dumps({'scope':principal.scope.model_dump(mode='json'),
                    'run_id':run_id,'completion_id':completion_id,'activation_id':row['activation_id'],
                    'accepted_run_revision':row['receipt']['outcome']['committed']['revision'],'canonical_result':True,
                    'retention_reservation_ids':[receipt['outcome']['binding']['reservation_id'] for receipt in row['reservations']],
                    'result':row['result']}))
                invocation = PreparedInvocation.model_validate_json(json.dumps(row['specification']))
                return ProducerSnapshot(invocation,completion,row['worker_id'],row['attempt_id'],row['fence']).to_wire()
            except (ValueError, KeyError, TypeError) as error:
                raise ProducerProofError("producer_record_inconsistent") from error
