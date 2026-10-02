"""Atomic owner-only accepted history; peer I/O never belongs inside these transactions."""

import hashlib
import json
from datetime import UTC, datetime

from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AcceptedGraphChange,
    DomainGraphSnapshot,
    DomainHead,
    DomainRevisionRef,
    GraphAuthoringProfile,
    GraphChangeDecision,
)
from sqlalchemy import text

from ..authoring.canonical import KnowledgeError, canonical, digest
from ..replay.accepted import AcceptedEdit
from ..replay.chain import GraphReplay
from .records import SCOPE, GraphProfile, ProposalDocument, graph_key

MAX_LOG_BYTES = 64 * 1024 * 1024
MAX_CHANGES = 10000


def lock_graph(connection, graph):
    raw = json.dumps(["knowledge", graph.scope.tenant_id, graph.scope.project_id, graph.graph_id], separators=(",", ":")).encode()
    key = int.from_bytes(hashlib.sha256(raw).digest()[:8], "big", signed=True)
    connection.execute(text("SELECT pg_advisory_xact_lock(:lock)"), {"lock": key})


class KnowledgeLedger:
    def __init__(self, engine, vocabulary, policy):
        self.engine = engine
        self.default_profile = GraphProfile(vocabulary, policy)

    @staticmethod
    def _proposal(connection, key):
        return connection.execute(text("SELECT * FROM knowledge.proposals WHERE " + SCOPE + " AND change_id=:change"), key).mappings().one_or_none()

    @staticmethod
    def _decision(connection, key):
        raw = connection.execute(text("SELECT canonical_bytes FROM knowledge.decisions WHERE " + SCOPE + " AND change_id=:change"), key).scalar_one_or_none()
        return None if raw is None else GraphChangeDecision.model_validate_json(bytes(raw))

    @staticmethod
    def _head(connection, graph):
        row = connection.execute(text("SELECT * FROM knowledge.heads WHERE " + SCOPE), graph_key(graph)).mappings().one_or_none()
        if row is None:
            return None
        snapshot = DomainRevisionRef(graph=graph, revision=row["revision"], sha256=row["snapshot_sha256"])
        change = AcceptedChangeRef(graph=graph, change_id=row["change_id"], position=row["revision"], sha256=row["change_sha256"])
        return DomainHead(snapshot=snapshot, change=change)

    def begin(self, principal, proposal):
        document = ProposalDocument.create(principal, proposal)
        with self.engine.begin() as connection:
            lock_graph(connection, proposal.graph)
            profile = connection.execute(text("SELECT 1 FROM knowledge.graph_profiles WHERE " + SCOPE), document.key).scalar_one_or_none()
            if profile is None:
                connection.execute(text("INSERT INTO knowledge.graph_profiles "
                    "(tenant_id,project_id,graph_id,vocabulary_sha256,policy_sha256,vocabulary_bytes,policy_bytes) "
                    "VALUES (:tenant,:project,:graph,:vocabulary_sha,:policy_sha,:vocabulary_bytes,:policy_bytes)"),
                    document.key | self.default_profile.storage())
            row = self._proposal(connection, document.key)
            if row is None:
                connection.execute(text("INSERT INTO knowledge.proposals "
                    "(tenant_id,project_id,graph_id,change_id,actor_id,request_sha256,canonical_bytes) "
                    "VALUES (:tenant,:project,:graph,:change,:actor,:sha,:body)"),
                    document.key | {"actor": document.actor_id, "sha": document.sha256, "body": document.raw})
                row = self._proposal(connection, document.key)
            document.require_same(row)
            return ProposalDocument.status(row, self._decision(connection, document.key))

    def status(self, principal, graph, change_id):
        principal.require("read_graph", graph.scope)
        key = graph_key(graph) | {"change": change_id}
        with self.engine.connect() as connection:
            row = self._proposal(connection, key)
            return None if row is None else ProposalDocument.status(row, self._decision(connection, key))

    def head(self, principal, graph):
        principal.require("read_graph", graph.scope)
        with self.engine.connect() as connection:
            return self._head(connection, graph)

    def profile(self, principal, graph):
        principal.require("read_graph", graph.scope)
        with self.engine.connect() as connection:
            row = connection.execute(text("SELECT * FROM knowledge.graph_profiles WHERE " + SCOPE), graph_key(graph)).mappings().one_or_none()
        profile = self.default_profile if row is None else GraphProfile.restore(row)
        return GraphAuthoringProfile(wire_version="1", graph=graph,
            vocabulary=profile.vocabulary.canonical_record(), vocabulary_reference=profile.vocabulary.reference,
            policy=profile.policy.reference, origin="configured_default" if row is None else "stored")

    def change(self, principal, reference):
        principal.require("read_graph", reference.graph.scope)
        with self.engine.connect() as connection:
            raw = connection.execute(text("SELECT canonical_bytes FROM knowledge.accepted_changes WHERE " + SCOPE +
                " AND position=:position AND change_id=:change AND change_sha256=:sha"), graph_key(reference.graph) |
                {"position": reference.position, "change": reference.change_id, "sha": reference.sha256}).scalar_one_or_none()
        if raw is None:
            return None
        record = AcceptedGraphChange.model_validate_json(bytes(raw))
        if (record.reference != reference or record.content.proposal.graph != reference.graph
                or record.content.proposal.change_id != reference.change_id
                or record.content.position != reference.position or digest(record.content) != reference.sha256):
            raise KnowledgeError("accepted_storage_mismatch")
        return record

    def snapshot(self, principal, reference):
        principal.require("read_graph", reference.graph.scope)
        with self.engine.connect() as connection:
            key = graph_key(reference.graph) | {"revision": reference.revision, "sha": reference.sha256}
            raw = connection.execute(text("SELECT c.canonical_bytes FROM knowledge.snapshot_publications p "
                "JOIN knowledge.rebuild_candidates c USING (tenant_id,project_id,graph_id,rebuild_id,candidate_id) "
                "WHERE p.tenant_id=:tenant AND p.project_id=:project AND p.graph_id=:graph "
                "AND c.revision=:revision AND c.snapshot_sha256=:sha"), key).scalar_one_or_none()
            if raw is None:
                raw = connection.execute(text("SELECT canonical_bytes FROM knowledge.snapshots WHERE " + SCOPE +
                    " AND revision=:revision AND snapshot_sha256=:sha"), key).scalar_one_or_none()
        if raw is None:
            return None
        record = DomainGraphSnapshot.model_validate_json(bytes(raw))
        if (record.reference != reference or record.content.graph != reference.graph
                or record.content.revision != reference.revision or digest(record.content) != reference.sha256):
            raise KnowledgeError("snapshot_storage_mismatch")
        return record

    def _load_state(self, graph):
        with self.engine.connect() as connection:
            row = connection.execute(text("SELECT * FROM knowledge.graph_profiles WHERE " + SCOPE), graph_key(graph)).mappings().one()
            profile = GraphProfile.restore(row)
            head = self._head(connection, graph)
            records, total = [], 0
            if head is not None:
                result = connection.execute(text("SELECT canonical_bytes FROM knowledge.accepted_changes WHERE " + SCOPE +
                    " AND position<=:position ORDER BY position"), graph_key(graph) | {"position": head.change.position},
                    execution_options={"stream_results": True})
                try:
                    for raw, in result:
                        total += len(raw)
                        if total > MAX_LOG_BYTES or len(records) >= MAX_CHANGES:
                            raise KnowledgeError("stored_history_limit")
                        records.append(bytes(raw))
                finally:
                    result.close()
        replay = GraphReplay(graph, profile.vocabulary, profile.policy).rebuild(
            AcceptedGraphChange.model_validate_json(raw) for raw in records)
        if replay.head != head:
            raise KnowledgeError("stored_head_mismatch")
        return replay

    @staticmethod
    def _save_decision(connection, document, decision):
        connection.execute(text("INSERT INTO knowledge.decisions "
            "(tenant_id,project_id,graph_id,change_id,outcome,canonical_bytes) "
            "VALUES (:tenant,:project,:graph,:change,:outcome,:body)"), document.key |
            {"outcome": decision.decision.outcome, "body": canonical(decision)})
        return decision

    def reject(self, principal, proposal, code):
        started = self.begin(principal, proposal)
        if started.decision is not None:
            return started.decision
        document = ProposalDocument.create(principal, proposal)
        with self.engine.begin() as connection:
            lock_graph(connection, proposal.graph)
            previous = self._decision(connection, document.key)
            if previous is not None:
                return previous
            return self._save_decision(connection, document, document.failed(code))

    def accept(self, principal, proposal, observation):
        started = self.begin(principal, proposal)
        if started.decision is not None:
            return started.decision
        document = ProposalDocument.create(principal, proposal)
        before = self._load_state(proposal.graph)
        if before.state.revision >= MAX_CHANGES:
            return self.reject(principal, proposal, "graph_change_limit")
        try:
            edit = AcceptedEdit.review(before.state, before.head, proposal, actor_id=principal.actor_id,
                                        observation=observation, accepted_at=datetime.now(UTC))
        except KnowledgeError as error:
            return self.reject(principal, proposal, str(error))
        log_bytes = canonical(edit.record)
        snapshot_bytes = canonical(edit.state.to_snapshot())
        if len(log_bytes) > 1048576 or len(snapshot_bytes) > 16777216:
            return self.reject(principal, proposal, "accepted_state_limit")
        with self.engine.begin() as connection:
            lock_graph(connection, proposal.graph)
            previous = self._decision(connection, document.key)
            if previous is not None:
                return previous
            if self._head(connection, proposal.graph) != before.head:
                return self._save_decision(connection, document, document.failed("stale_head"))
            size = connection.execute(text("SELECT COALESCE(SUM(octet_length(canonical_bytes)),0) FROM knowledge.accepted_changes WHERE " + SCOPE), document.key).scalar_one()
            if size + len(log_bytes) > MAX_LOG_BYTES:
                return self._save_decision(connection, document, document.failed("graph_history_bytes_limit"))
            binding = document.key | {"position": edit.state.revision, "prior": None if before.head is None else before.head.change.position,
                "change_sha": edit.record.reference.sha256, "snapshot_sha": edit.state.reference.sha256}
            connection.execute(text("INSERT INTO knowledge.accepted_changes "
                "(tenant_id,project_id,graph_id,position,prior_position,change_id,change_sha256,snapshot_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:graph,:position,:prior,:change,:change_sha,:snapshot_sha,:body)"), binding | {"body": log_bytes})
            connection.execute(text("INSERT INTO knowledge.snapshots "
                "(tenant_id,project_id,graph_id,revision,snapshot_sha256,change_id,change_sha256,canonical_bytes) "
                "VALUES (:tenant,:project,:graph,:position,:snapshot_sha,:change,:change_sha,:body)"), binding | {"body": snapshot_bytes})
            connection.execute(text("INSERT INTO knowledge.heads "
                "(tenant_id,project_id,graph_id,revision,snapshot_sha256,change_id,change_sha256) "
                "VALUES (:tenant,:project,:graph,:position,:snapshot_sha,:change,:change_sha) "
                "ON CONFLICT (tenant_id,project_id,graph_id) DO UPDATE SET revision=EXCLUDED.revision, "
                "snapshot_sha256=EXCLUDED.snapshot_sha256,change_id=EXCLUDED.change_id,change_sha256=EXCLUDED.change_sha256"), binding)
            return self._save_decision(connection, document, document.accepted(edit.head))
