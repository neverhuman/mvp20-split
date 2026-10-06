"""Planning-owned immutable proposal records; no peer call inside SQL."""
from pydantic import TypeAdapter
from amphora_contracts_core import Identifier
from sqlalchemy import text
from .document import TopologyDocument
from .values import encoded, require

KEY='tenant_id=:tenant AND project_id=:project AND proposal_id=:proposal'


class TopologyStoreUnavailable(RuntimeError):
    pass


class TopologyJournal:
    def __init__(self, engine):
        self.engine=engine

    @staticmethod
    def params(principal, proposal_id):
        TypeAdapter(Identifier).validate_python(proposal_id,strict=True)
        return {'tenant':principal.scope.tenant_id,'project':principal.scope.project_id,'proposal':proposal_id,'actor':principal.actor_id}

    @staticmethod
    def decode(principal,row):
        if row is None:return None
        if row['actor_id']!=principal.actor_id:raise PermissionError('planning_access_denied')
        try:
            record=TopologyDocument.load(bytes(row['record_bytes']))
            ref=record.projection.reference
            require(record.sha256==row['record_sha256'] and record.actor_id==row['actor_id'] and
                    ref.scope==principal.scope and ref.proposal_id==row['proposal_id'],'topology_stored_identity')
        except (ValueError,TypeError,KeyError,RecursionError) as error:
            raise TopologyStoreUnavailable('topology_stored_record_invalid') from error
        return record

    def read(self, principal, proposal_id):
        principal.require('read_topology',principal.scope)
        with self.engine.connect() as conn:
            row=conn.execute(text('SELECT * FROM planning.topology_proposals WHERE '+KEY),self.params(principal,proposal_id)).mappings().first()
            return self.decode(principal,row)

    def register(self, principal, supplied):
        record=TopologyDocument.load(supplied.canonical)
        ref=record.projection.reference
        principal.require('propose_topology',ref.scope)
        if record.actor_id!=principal.actor_id:raise PermissionError('planning_access_denied')
        params=self.params(principal,ref.proposal_id)
        with self.engine.begin() as conn:
            token=encoded(['planning-topology-v1',params['tenant'],params['project'],params['proposal']]).decode()
            conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:token,0))'),{'token':token})
            old=self.decode(principal,conn.execute(text('SELECT * FROM planning.topology_proposals WHERE '+KEY),params).mappings().first())
            if old is not None:
                require(old==record,'topology_proposal_conflict')
                return old
            conn.execute(text('INSERT INTO planning.topology_proposals (tenant_id,project_id,proposal_id,actor_id,record_sha256,record_bytes) '
                'VALUES (:tenant,:project,:proposal,:actor,:sha,:body)'),{**params,'sha':record.sha256,'body':record.canonical})
        return record
