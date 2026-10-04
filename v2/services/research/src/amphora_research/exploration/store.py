"""Bounded owner-local existence read; immutable selected rows need no mutable watermark."""

from sqlalchemy import bindparam, text

from .query import require


class ObservationSelectionIndex:
    def __init__(self, engine):
        self.engine = engine

    def contains_all(self, scope, references):
        require(
            type(references) is tuple and 1 <= len(references) <= 128, "selection_bound"
        )
        require(all(ref.scope == scope for ref in references), "selection_scope")
        identities = tuple((ref.observation_id, ref.revision) for ref in references)
        require(len(set(identities)) == len(identities), "duplicate_observation")
        statement = text(
            "SELECT identity_id,revision FROM research.observation_revisions "
            "WHERE tenant_id=:tenant AND project_id=:project AND (identity_id,revision) IN :identities"
        ).bindparams(bindparam("identities", expanding=True))
        with self.engine.connect() as connection:
            rows = connection.execute(
                statement,
                {
                    "tenant": scope.tenant_id,
                    "project": scope.project_id,
                    "identities": identities,
                },
            ).all()
        return set(map(tuple, rows)) == set(identities)
