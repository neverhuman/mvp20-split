"""Exact owner-local material-state links; no implicit current selection or peer access."""
from amphora_contracts_research import MaterialStateRevision
from sqlalchemy import text

from ..identity.questions import ResearchIdentityError


def read(connection, reference):
    raw = connection.execute(text("SELECT canonical_bytes FROM research.material_state_revisions "
        "WHERE tenant_id=:tenant AND project_id=:project AND identity_id=:id AND revision=:revision"),
        {"tenant":reference.scope.tenant_id,"project":reference.scope.project_id,
         "id":reference.material_state_id,"revision":reference.revision}).scalar_one_or_none()
    return None if raw is None else MaterialStateRevision.model_validate_json(bytes(raw))


def require_sample_state(connection, sample):
    state = read(connection,sample.material_state)
    if state is None:
        raise ResearchIdentityError("unknown_material_state")
    if state.candidate != sample.candidate:
        raise ResearchIdentityError("sample_material_candidate_mismatch")


def link_sample(connection, sample):
    ref, state = sample.reference,sample.material_state
    connection.execute(text("INSERT INTO research.sample_material_states "
        "(tenant_id,project_id,sample_id,sample_revision,state_id,state_revision) "
        "VALUES (:tenant,:project,:sample,:sample_revision,:state,:state_revision)"),
        {"tenant":ref.scope.tenant_id,"project":ref.scope.project_id,"sample":ref.sample_id,"sample_revision":ref.revision,
         "state":state.material_state_id,"state_revision":state.revision})
