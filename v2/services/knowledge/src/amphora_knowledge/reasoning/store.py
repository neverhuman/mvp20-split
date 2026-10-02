"""Short owner transactions; no evaluation or peer calls under the graph lock."""

import hashlib

from amphora_contracts_knowledge import ReasoningRuleSet, ReasoningStatus
from sqlalchemy import text

from ..access import Principal
from ..authoring.canonical import KnowledgeError, canonical, digest
from ..persistence.ledger import lock_graph
from ..persistence.records import SCOPE
from ..rebuild.store import candidate_head
from .profile import RuleProfile, raw
from .requests import RegisteredEvaluation, RequestDocument

REQUEST_SCOPE = SCOPE + " AND request_id=:request"
PROFILE_SCOPE = SCOPE + " AND rule_set_id=:rules AND version=:version"


class ReasoningStore:
    def __init__(self, engine):
        self.engine = engine

    @staticmethod
    def _existing(connection, document):
        row = connection.execute(text("SELECT * FROM knowledge.reasoning_intents WHERE " + REQUEST_SCOPE),
            document.key).mappings().one_or_none()
        if row is None:
            return None
        document.require_same(row)
        key = document.key | {"rules": row["rule_set_id"], "version": row["version"]}
        stored = connection.execute(text("SELECT * FROM knowledge.reasoning_profiles WHERE " + PROFILE_SCOPE), key).mappings().one()
        profile = RuleProfile(ReasoningRuleSet.model_validate_json(bytes(stored["canonical_bytes"])))
        if (profile.reference != document.request.rule_set or digest(profile.record) != stored["profile_sha256"]
                or profile.reference.sha256 != row["profile_sha256"]
                or canonical(profile.record) != bytes(stored["canonical_bytes"])):
            raise KnowledgeError("reasoning_storage_mismatch")
        snapshot = connection.execute(text("SELECT * FROM knowledge.snapshots WHERE " + SCOPE +
            " AND revision=:revision AND snapshot_sha256=:snapshot"), document.key |
            {"revision": row["revision"], "snapshot": row["snapshot_sha256"]}).mappings().one()
        head = candidate_head(document.request.snapshot.graph, snapshot)
        if head.snapshot != document.request.snapshot:
            raise KnowledgeError("reasoning_storage_mismatch")
        decision = connection.execute(text("SELECT * FROM knowledge.reasoning_decisions WHERE " + REQUEST_SCOPE),
            document.key).mappings().one_or_none()
        status = document.pending()
        if decision is not None:
            body = bytes(decision["canonical_bytes"])
            status = ReasoningStatus.model_validate_json(body)
            if (status.request != document.request or status.actor_id != document.actor_id or status.decision is None
                    or status.decision.outcome != decision["outcome"]
                    or hashlib.sha256(body).hexdigest() != decision["decision_sha256"]):
                raise KnowledgeError("reasoning_storage_mismatch")
            if status.decision.outcome == "evaluated" and status.decision.result.request != document.request:
                raise KnowledgeError("reasoning_storage_mismatch")
        return RegisteredEvaluation(document, profile, head, status)

    def begin(self, principal, request, profile=None):
        document = RequestDocument.authorized(principal, request)
        graph = document.request.snapshot.graph
        with self.engine.begin() as connection:
            lock_graph(connection, graph)
            existing = self._existing(connection, document)
            if existing is not None:
                return existing
            if profile is None or profile.reference != request.rule_set:
                raise KnowledgeError("reasoning_profile_unavailable")
            body = canonical(profile.record)
            if len(body) > 2097152:
                raise KnowledgeError("reasoning_profile_size_limit")
            key = document.key | {"rules": profile.reference.rule_set_id, "version": profile.reference.version,
                "profile_sha": profile.reference.sha256, "profile_body": body}
            exists = connection.execute(text("SELECT 1 FROM knowledge.snapshots WHERE " + SCOPE +
                " AND revision=:revision AND snapshot_sha256=:snapshot"), key |
                {"revision": request.snapshot.revision, "snapshot": request.snapshot.sha256}).scalar_one_or_none()
            if exists is None:
                raise KnowledgeError("reasoning_snapshot_unavailable")
            previous = connection.execute(text("SELECT canonical_bytes FROM knowledge.reasoning_profiles WHERE " +
                PROFILE_SCOPE), key).scalar_one_or_none()
            if previous is not None and bytes(previous) != body:
                raise KnowledgeError("reasoning_profile_identity_conflict")
            if previous is None:
                connection.execute(text("INSERT INTO knowledge.reasoning_profiles "
                    "(tenant_id,project_id,graph_id,rule_set_id,version,profile_sha256,canonical_bytes) "
                    "VALUES (:tenant,:project,:graph,:rules,:version,:profile_sha,:profile_body)"), key)
            connection.execute(text("INSERT INTO knowledge.reasoning_intents "
                "(tenant_id,project_id,graph_id,request_id,actor_id,request_sha256,canonical_bytes,rule_set_id,version,profile_sha256,revision,snapshot_sha256) "
                "VALUES (:tenant,:project,:graph,:request,:actor,:sha,:body,:rules,:version,:profile_sha,:revision,:snapshot)"),
                key | {"actor": document.actor_id, "sha": document.sha256, "body": document.body,
                    "revision": request.snapshot.revision, "snapshot": request.snapshot.sha256})
            return self._existing(connection, document)

    def read(self, principal, graph, request_id):
        from ..persistence.records import graph_key

        principal.require("read_graph", graph.scope)
        key = graph_key(graph) | {"request": request_id}
        with self.engine.connect() as connection:
            row = connection.execute(text("SELECT * FROM knowledge.reasoning_intents WHERE " + REQUEST_SCOPE), key).mappings().one_or_none()
            if row is None:
                return None
            from amphora_contracts_knowledge import ReasoningRequest

            request = ReasoningRequest.model_validate_json(bytes(row["canonical_bytes"]))
            actor = Principal(row["actor_id"], graph.scope, frozenset({"reason_graph"}))
            document = RequestDocument.authorized(actor, request)
            if document.key != key:
                raise KnowledgeError("reasoning_storage_mismatch")
            return self._existing(connection, document).status

    def finish(self, registered, decision):
        document = registered.document
        status = ReasoningStatus.model_validate(raw(document.pending().model_copy(update={"decision": decision})))
        if status.decision is None:
            raise KnowledgeError("reasoning_terminal_required")
        if status.decision.outcome == "evaluated" and status.decision.result.request != document.request:
            raise KnowledgeError("reasoning_result_request_mismatch")
        body = canonical(status)
        if len(body) > 20971520:
            raise KnowledgeError("reasoning_result_size_limit")
        with self.engine.begin() as connection:
            lock_graph(connection, document.request.snapshot.graph)
            previous = self._existing(connection, document)
            if previous is None:
                raise KnowledgeError("reasoning_intent_missing")
            if previous.status.decision is not None:
                return previous.status
            connection.execute(text("INSERT INTO knowledge.reasoning_decisions "
                "(tenant_id,project_id,graph_id,request_id,outcome,decision_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:graph,:request,:outcome,:sha,:body)"), document.key |
                {"outcome": status.decision.outcome, "sha": hashlib.sha256(body).hexdigest(), "body": body})
            return status
