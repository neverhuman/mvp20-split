"""Winner-first readback without replacing original intake receipts."""
from sqlalchemy import text

from ..context.policy import require
from .original import OriginalFulfillment
from .verification import lookup


def current_fulfillment(conn, principal, capability):
    row = conn.execute(text('SELECT f.* FROM planning.capability_fulfillments f '
        'LEFT JOIN planning.capability_verifications v ON v.tenant_id=f.tenant_id '
        'AND v.project_id=f.project_id AND v.fulfillment_id=f.fulfillment_id '
        'WHERE f.tenant_id=:tenant AND f.project_id=:project AND f.actor_id=:actor AND f.request_id=:request '
        "ORDER BY CASE WHEN v.status='verified' THEN 0 ELSE 1 END, f.recorded_at DESC, f.fulfillment_id DESC LIMIT 1"),
        {'tenant': principal.scope.tenant_id, 'project': principal.scope.project_id,
         'actor': principal.actor_id, 'request': capability.reference.request_id}).mappings().one_or_none()
    if row is None:
        return None
    original = OriginalFulfillment.restore(row)
    require(original.capability == capability, 'fulfillment_original_capability_changed')
    verified = lookup(conn, original)
    return original.receipt if verified is None else verified.receipt
