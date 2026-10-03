"""Current authorized binding metadata; original request replay is a separate boundary."""

from ...source_rights.ledger import SourceRights
from ..storage.records import authorize
from ..validation import identifier, require
from .records import published


class BindingViews:
    def __init__(self, engine):
        self.engine = engine
        self.rights = SourceRights(engine)

    def read(self, principal, binding_id):
        authorize(principal, "representation_read")
        principal.require("read")
        identifier(binding_id)
        with self.engine.begin() as connection:
            binding = published(connection, principal, binding_id)
            require(binding is not None, "representation_binding_missing")
            self.rights.authorize(connection, principal, (binding.vector.artifact_id,), use="read")
            return binding
