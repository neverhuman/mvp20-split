"""Scoped keyset discovery and one bounded read-only evidence review per turn."""
from dataclasses import dataclass
from sqlalchemy import text

from .failures import retryable

QUERY = '''SELECT f.fulfillment_id FROM planning.capability_fulfillments f
 WHERE f.tenant_id=:tenant AND f.project_id=:project AND f.actor_id=:actor
 AND NOT EXISTS (SELECT 1 FROM planning.capability_verifications v
 WHERE v.tenant_id=f.tenant_id AND v.project_id=f.project_id AND v.fulfillment_id=f.fulfillment_id)
 AND f.fulfillment_id>:after ORDER BY f.fulfillment_id LIMIT 1'''


@dataclass(frozen=True)
class FulfillmentTick:
    status: str
    fulfillment_id: str


class FulfillmentWorker:
    def __init__(self, verifier):
        self.verifier, self.cursors = verifier, {}

    def tick(self, principal):
        principal.require('execute_curations', principal.scope)
        key = (principal.scope.tenant_id, principal.scope.project_id, principal.actor_id)
        parameters = dict(tenant=key[0], project=key[1], actor=key[2])
        after = self.cursors.get(key, '')
        with self.verifier.engine.connect() as conn:
            identifier = conn.execute(text(QUERY), {**parameters, 'after': after}).scalar_one_or_none()
            if identifier is None and after:
                identifier = conn.execute(text(QUERY), {**parameters, 'after': ''}).scalar_one_or_none()
        self.cursors[key] = identifier or ''
        if identifier is None:
            return None
        try:
            receipt = self.verifier.verify(principal, identifier)
            return FulfillmentTick('fulfillment_' + receipt.status, identifier)
        except (ValueError, OSError) as error:
            if not retryable(error):
                raise
            return FulfillmentTick('fulfillment_pending', identifier)
