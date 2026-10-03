"""Material-state revisions retain exact candidate identity in one owner transaction."""
from amphora_contracts_research import MaterialStateRevision
from sqlalchemy import text

from ..persistence.revisions import RevisionJournal, ScientificStoreError
from .wire import from_wire


def link_candidate(connection, record, key):
    candidate = record.candidate
    exists = connection.execute(text("SELECT 1 FROM research.identity_records WHERE tenant_id=:tenant AND project_id=:project "
        "AND kind='candidate' AND identity_id=:candidate AND revision=:candidate_revision"),
        key|{"candidate":candidate.candidate_id,"candidate_revision":candidate.revision}).scalar_one_or_none()
    if exists is None:
        raise ScientificStoreError("unknown_material_candidate")
    connection.execute(text("INSERT INTO research.material_state_candidates "
        "(tenant_id,project_id,state_id,state_revision,candidate_id,candidate_revision) "
        "VALUES (:tenant,:project,:id,:revision,:candidate,:candidate_revision)"),
        key|{"candidate":candidate.candidate_id,"candidate_revision":candidate.revision})


class MaterialStateStore(RevisionJournal):
    def __init__(self, engine):
        super().__init__(engine,MaterialStateRevision,from_wire,link_candidate)
