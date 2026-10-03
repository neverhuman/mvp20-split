"""Actor-scoped request aliases; fresh admission rights and immutable historical replay."""

from amphora_contracts_representations import (
    EncodeSourceRequest,
    EncodingPending,
    EncodingPublished,
    EncodingStatus,
)
from sqlalchemy import text

from ...persistence.evidence_records import SCOPE
from ...source_rights.ledger import SourceRights
from ..mapping import _validated
from ..storage.records import authorize, load_profile
from ..validation import canonical_record, require
from .identity import SourceBindingIdentity
from .records import event_bytes, lock_binding, published
from .source import PreparedBindingSource

REQUEST = SCOPE + " AND actor_id=:actor AND encoding_id=:encoding"


class BindingRequests:
    def __init__(self, engine):
        self.engine = engine
        self.rights = SourceRights(engine)

    @staticmethod
    def _status(connection, principal, request):
        binding_id = SourceBindingIdentity.prepare(principal, request).binding_id
        result = published(connection, principal, binding_id)
        outcome = (
            EncodingPending(state="pending")
            if result is None
            else EncodingPublished(state="published", binding=result)
        )
        return EncodingStatus(wire_version="1", request=request, actor_id=principal.actor_id, outcome=outcome)

    def read(self, principal, encoding_id):
        authorize(principal, "representation_read")
        with self.engine.connect() as connection:
            raw = connection.execute(
                text("SELECT canonical_bytes FROM artifacts.encoding_requests WHERE " + REQUEST),
                principal.bindings | {"encoding": encoding_id},
            ).scalar_one_or_none()
            if raw is None:
                return None
            request = EncodeSourceRequest.model_validate_json(bytes(raw))
            require(request.encoding_id == encoding_id, "representation_request_conflict")
            return self._status(connection, principal, request)

    def register(self, principal, request, prepared):
        authorize(principal, "representation_encode")
        request = _validated(request, EncodeSourceRequest)
        require(type(prepared) is PreparedBindingSource, "representation_prepared_required")
        identity = SourceBindingIdentity.prepare(principal, request)
        require(identity == prepared.identity, "representation_prepared_identity")
        body = canonical_record(request)
        with self.engine.begin() as connection:
            self.rights.fence(connection, principal, prepared.rights)
            key = lock_binding(connection, principal, identity.binding_id)
            require(
                load_profile(connection, principal, identity.profile) == prepared.profile,
                "representation_profile_conflict",
            )
            # The source revision and profile FKs pin immutable histories, never their moving heads.
            ref = identity.source.source
            connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_binding_jobs "
                    "(tenant_id,project_id,binding_id,actor_id,profile_id,version,profile_sha256,source_id,revision_id,"
                    "work_sha256,canonical_bytes) VALUES (:tenant,:project,:binding,:actor,:profile,:version,"
                    ":digest,:source,:revision,:work,:body) ON CONFLICT DO NOTHING"
                ),
                key
                | {
                    "profile": identity.profile.profile_id,
                    "version": identity.profile.version,
                    "digest": identity.profile.sha256,
                    "source": ref.source_id,
                    "revision": ref.revision_id,
                    "work": prepared.work.sha256,
                    "body": body,
                },
            )
            connection.execute(
                text(
                    "INSERT INTO artifacts.encoding_requests "
                    "(tenant_id,project_id,actor_id,encoding_id,binding_id,canonical_bytes,rights_epoch) VALUES "
                    "(:tenant,:project,:actor,:encoding,:binding,:body,:rights) ON CONFLICT DO NOTHING"
                ),
                key
                | {
                    "encoding": request.encoding_id,
                    "body": body,
                    "rights": event_bytes(prepared.rights.heads),
                },
            )
            actual = connection.execute(
                text("SELECT canonical_bytes FROM artifacts.encoding_requests WHERE " + REQUEST),
                key | {"encoding": request.encoding_id},
            ).scalar_one()
            require(bytes(actual) == body, "representation_request_conflict")
            return self._status(connection, principal, request)
