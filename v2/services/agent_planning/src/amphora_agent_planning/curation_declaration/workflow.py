"""Existing bounded derived-upload driver; configuration is not a model capture."""
from ..context.policy import require
from ..publication.driver import drive_upload
from ..publication.transport import PublicationTransport


class DeclarationTransport(PublicationTransport):
    media_types = frozenset({'application/json', 'text/plain'})


class DeclarationPublisher:
    def __init__(self, journal, client):
        self.journal, self.client = journal, client

    def publish(self, principal, lease, *, policy=None, original=None):
        require(self.client.identity.actor_id == principal.actor_id and self.client.identity.scope == principal.scope,
                'curation_declaration_client')
        state = self.journal.read(principal, lease.curation_id)
        if state is None:
            require(policy is not None and original is not None, 'curation_declaration_input_required')
            state = self.journal.register(principal, lease, policy, original)
        return drive_upload(self.journal, self.client, principal, lease, state)
