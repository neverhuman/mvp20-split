"""Experiment revisions verify exact persisted sample/state records before linking them."""
from amphora_contracts_research import ExperimentDefinition, SampleIdentity
from sqlalchemy import text

from ..material_state.links import read as read_state
from ..persistence.revisions import RevisionJournal, ScientificStoreError
from .wire import from_wire


def link_samples(connection, record, key):
    for item in record.samples:
        ref = item.sample.reference
        params = key|{"sample":ref.sample_id,"sample_revision":ref.revision}
        raw = connection.execute(text("SELECT canonical_bytes FROM research.identity_records "
            "WHERE tenant_id=:tenant AND project_id=:project AND kind='sample' AND identity_id=:sample AND revision=:sample_revision"),
            params).scalar_one_or_none()
        if raw is None:
            raise ScientificStoreError("unknown_experiment_sample")
        if SampleIdentity.model_validate_json(bytes(raw)) != item.sample:
            raise ScientificStoreError("experiment_sample_record_mismatch")
        if item.state is not None and read_state(connection,item.state.reference) != item.state:
            raise ScientificStoreError("experiment_state_record_mismatch")
        connection.execute(text("INSERT INTO research.experiment_samples "
            "(tenant_id,project_id,experiment_id,experiment_revision,sample_id,sample_revision) "
            "VALUES (:tenant,:project,:id,:revision,:sample,:sample_revision)"),params)


class ExperimentStore(RevisionJournal):
    def __init__(self, engine):
        super().__init__(engine,ExperimentDefinition,from_wire,link_samples)
