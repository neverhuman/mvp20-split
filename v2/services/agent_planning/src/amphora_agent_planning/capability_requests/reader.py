"""Scoped read projection over Planning's immutable original capture/progress."""
from sqlalchemy import text

from ..curation_intake.record import OriginalCuration
from ..curation_jobs.journal import current
from .projection import CapabilityAddress, CurationCapabilities


def load_original(conn, principal, request_id):
    """Private projection; callers enforce their own operation-specific grant."""
    address = CapabilityAddress.parse(request_id)
    if address is None:
        return None
    row = conn.execute(text('SELECT * FROM planning.curation_requests WHERE '
        'tenant_id=:tenant AND project_id=:project AND actor_id=:actor AND curation_id=:curation'),
        {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
         'actor': principal.actor_id, 'curation': address.curation_id}).mappings().one_or_none()
    if row is None:
        return None
    original = OriginalCuration.restore(row)
    progress = current(conn, original)
    return CurationCapabilities.bind(progress.view if progress is not None else original.view()).at(address)


class CapabilityRequestReader:
    def __init__(self, engine):
        self.engine = engine

    def read(self, principal, request_id):
        principal.require('read_capabilities', principal.scope)
        with self.engine.connect() as conn:
            projected = load_original(conn, principal, request_id)
            if projected is None:
                return None
            from ..capability_fulfillment.readback import current_fulfillment
            return projected.view(current_fulfillment(conn, principal, projected))
