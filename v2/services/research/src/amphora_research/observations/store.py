"""Preserve reported observations, including unmatched claims; storage is not acceptance."""
from amphora_contracts_research import ObservationRevision

from ..persistence.revisions import RevisionJournal
from .wire import from_wire


def preserve_claims(connection, record, key):
    # Deliberately no FK from untrusted report claims to scientific owner records.
    # Authenticated ingestion and explicit reconciliation are separate gates.
    return None


class ObservationStore(RevisionJournal):
    def __init__(self, engine):
        super().__init__(engine,ObservationRevision,from_wire,preserve_claims)
