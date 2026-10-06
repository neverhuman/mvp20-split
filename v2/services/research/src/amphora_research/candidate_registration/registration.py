"""Current peer read precedes an atomic immutable owner registration."""

import hashlib

from amphora_contracts_research import CandidateRevision, CandidateRevisionRef
from sqlalchemy import text

from ..assessment.policy import AssessmentError
from ..assessment.reader import AssessmentPeerUnavailable
from ..identity.questions import ResearchIdentityError
from ..persistence.ledger import IdentityDocument
from .profiles import CandidateRegistrationError

ACTIONS = frozenset({"declare_candidate", "read_candidate"})


class CandidateRegistrar:
    def __init__(self, ledger, profiles, reader_factory):
        self.ledger, self.profiles, self.reader_factory = (
            ledger,
            profiles,
            reader_factory,
        )

    def register(self, principal, record):
        if type(record) is not CandidateRevision:
            raise CandidateRegistrationError("candidate_record_kind_invalid")
        record = CandidateRevision.model_validate_json(record.model_dump_json())
        principal.require("declare_candidate", record.reference.scope)
        if (
            not isinstance(principal.actor_id, str)
            or not 1 <= len(principal.actor_id) <= 128
        ):
            raise CandidateRegistrationError("candidate_actor_invalid")
        try:
            document = IdentityDocument.from_record(principal.scope, record)
            self.profiles.admit(record.representation)
            # A fresh reader per attempt observes rights now; no peer call occurs under SQL.
            body = self.reader_factory(principal.scope).read(record.representation)
            self.profiles.validate(record.representation, body)
            with self.ledger.engine.begin() as connection:
                created = self.ledger.publish_prepared(connection, document)
                connection.execute(
                    text(
                        "INSERT INTO research.candidate_registrations "
                        "(tenant_id,project_id,kind,identity_id,revision,actor_id,record_sha256,preexisting) "
                        "VALUES (:tenant,:project,:kind,:id,:revision,:actor,:digest,:preexisting) "
                        "ON CONFLICT (tenant_id,project_id,kind,identity_id,revision) DO NOTHING"
                    ),
                    document.key()
                    | {
                        "actor": principal.actor_id,
                        "digest": hashlib.sha256(document.canonical_bytes).hexdigest(),
                        "preexisting": not created,
                    },
                )
            return document.record
        except AssessmentPeerUnavailable:
            raise
        except (AssessmentError, ResearchIdentityError) as error:
            raise CandidateRegistrationError(str(error)) from error


class CandidateReader:
    def __init__(self, ledger):
        self.ledger = ledger

    def read(self, principal, reference):
        reference = CandidateRevisionRef.model_validate_json(
            reference.model_dump_json()
        )
        principal.require("read_candidate", reference.scope)
        return self.ledger.read(
            reference.scope, "candidate", reference.candidate_id, reference.revision
        )
