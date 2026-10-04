"""First public registration and immutable identities commit atomically."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from sqlalchemy import text

from ..identity.questions import ResearchIdentityError
from ..persistence.ledger import IdentityDocument, IdentityLedger

ACTIONS = frozenset({"declare_question", "declare_evidence_need"})


class DeclarationError(ValueError):
    """Safe owner policy code; never includes input contents."""


@dataclass(frozen=True)
class Registration:
    document: IdentityDocument
    actor_id: str

    @classmethod
    def authorized(cls, principal, record):
        if type(record) not in (ResearchQuestion, EvidenceNeed):
            raise DeclarationError("declaration_kind_invalid")
        # Revalidate even for private callers using model_copy/model_construct.
        record = type(record).model_validate_json(record.model_dump_json())
        principal.require("declare_question" if type(record) is ResearchQuestion else
                          "declare_evidence_need", record.reference.scope)
        if not isinstance(principal.actor_id, str) or not 1 <= len(principal.actor_id) <= 128:
            raise DeclarationError("declaration_actor_invalid")
        return cls(IdentityDocument.from_record(principal.scope, record), principal.actor_id)

    def metadata(self, created):
        return self.document.key() | {"actor": self.actor_id,
            "digest": hashlib.sha256(self.document.canonical_bytes).hexdigest(),
            "preexisting": not created}


class DeclarationRegistrar:
    def __init__(self, ledger: IdentityLedger):
        self.ledger = ledger

    def register(self, principal, record):
        try:
            registration = Registration.authorized(principal, record)
            with self.ledger.engine.begin() as connection:
                created = self.ledger.publish_prepared(connection, registration.document)
                # The ledger identity lock also serializes registration/replay.
                connection.execute(text("INSERT INTO research.declaration_registrations "
                    "(tenant_id,project_id,kind,identity_id,revision,actor_id,record_sha256,preexisting) "
                    "VALUES (:tenant,:project,:kind,:id,:revision,:actor,:digest,:preexisting) "
                    "ON CONFLICT (tenant_id,project_id,kind,identity_id,revision) DO NOTHING"),
                    registration.metadata(created))
            return registration.document.record
        except ResearchIdentityError as error:
            raise DeclarationError(str(error)) from error
