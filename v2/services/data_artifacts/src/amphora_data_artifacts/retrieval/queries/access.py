"""Current source authority around external query I/O; quality never grants or denies it."""

from dataclasses import dataclass

from ...source_rights.ledger import SourceRights
from ...source_rights.model import RightsError
from ..validation import require

DENIED = {"rights_revoked", "rights_expired", "rights_use_denied"}


def uses(connection, principal, binding, *, processing=True):
    rights = SourceRights(None)
    modes = ("read", "process") if processing else ("read",)
    return tuple(rights.authorize(connection, principal, (binding.vector.artifact_id,), use=mode) for mode in modes)


@dataclass(frozen=True, slots=True)
class QueryAccess:
    query_rights: tuple
    eligible: tuple
    target_rights: tuple

    @classmethod
    def capture(cls, connection, principal, plan):
        SourceRights.lock(connection, principal)
        query_rights = uses(connection, principal, plan.query)
        eligible, snapshots = [], []
        for binding in plan.policy.select(plan.generation.manifest):
            try:
                current = uses(connection, principal, binding)
            except RightsError as error:
                if str(error) not in DENIED:
                    raise
                continue
            eligible.append(binding)
            snapshots.append(current)
        return cls(query_rights, tuple(eligible), tuple(snapshots))

    def fence(self, connection, principal, plan):
        current = self.capture(connection, principal, plan)
        require(current == self, "retrieval_rights_changed")

    def descriptor(self):
        def snapshot(value):
            return {"artifacts": value.artifacts, "use": value.use, "heads": value.heads}
        return {
            "format": "data.retrieval-access.v1",
            "query": [snapshot(s) for s in self.query_rights],
            "eligible": [b.reference.model_dump(mode="json") for b in self.eligible],
            "rights": [[snapshot(s) for s in pair] for pair in self.target_rights],
        }


def authorize_history(connection, principal, record):
    """Historical source identities still require present read permission; never rerank."""
    SourceRights.lock(connection, principal)
    uses(connection, principal, record.plan.query, processing=False)
    members = {b.reference: b for b in record.plan.generation.manifest.bindings}
    for match in record.matches:
        uses(connection, principal, members[match.binding], processing=False)
