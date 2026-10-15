"""Immutable owner-local catalog membership; group status remains on the root."""

from amphora_contracts_artifact_retention import DerivedClosureReservationReceipt
from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from ..publication.model import UploadError
from ..publication.uploads import SCOPE
from ..source_rights.ancestry import identities
from ..source_rights.model import RightsError
from .model import ProtectedClosure


def _reference(row, scope):
    return ArtifactRef(artifact_id=row["artifact_id"], scope=scope, sha256=row["content_sha256"],
                       size_bytes=row["size_bytes"], media_type=row["media_type"], schema_ref=row["schema_ref"])


def discover(conn, principal, root):
    if root.scope != principal.scope:
        raise UploadError("retention_closure_binding")
    try:
        members = identities(conn, principal, (root.artifact_id,))
    except RightsError as error:
        reason = "retention_lineage_cycle" if str(error) == "rights_lineage_cycle" else "retention_closure_limit"
        raise UploadError(reason) from None
    rows = conn.execute(text("SELECT * FROM artifacts.catalog WHERE " + SCOPE +
        " AND artifact_id=ANY(:members) ORDER BY artifact_id"),
        {**principal.bindings, "members": list(members)}).mappings().all()
    if len(rows) != len(members):
        raise UploadError("artifact_unavailable")
    return ProtectedClosure(root, tuple(_reference(row, principal.scope) for row in rows))


def load(conn, principal, reservation):
    params = {**principal.bindings, "reservation": reservation.binding.reservation_id}
    row = conn.execute(text("SELECT * FROM artifacts.retention_closures WHERE " + SCOPE +
                            " AND reservation_id=:reservation"), params).mappings().one_or_none()
    if row is None:
        raise UploadError("retention_closure_unavailable")
    return DerivedClosureReservationReceipt(profile=row["profile"], reservation=reservation.receipt(),
        artifact_count=row["artifact_count"], members_sha256=row["members_sha256"])


def persist(conn, principal, reservation, closure):
    params = {**principal.bindings, "reservation": reservation.binding.reservation_id,
              "count": len(closure.members), "digest": closure.digest}
    conn.execute(text("INSERT INTO artifacts.retention_closures "
        "(tenant_id,project_id,reservation_id,profile,artifact_count,members_sha256) "
        "VALUES (:tenant,:project,:reservation,'derived-closure-retention-v1',:count,:digest)"), params)
    conn.execute(text("INSERT INTO artifacts.retention_closure_members "
        "(tenant_id,project_id,reservation_id,ordinal,artifact_id,content_sha256) "
        "VALUES (:tenant,:project,:reservation,:ordinal,:artifact,:digest)"),
        [{**params, "ordinal": i, "artifact": r.artifact_id, "digest": r.sha256} for i, r in enumerate(closure.members)])
