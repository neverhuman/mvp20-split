"""Explicit local fixture host; startup validates ownership and never migrates."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from amphora_contracts_core import Scope
from amphora_contracts_runtime import AdmitFixtureRun
from amphora_contracts_tools import ToolDescriptor
from sqlalchemy import create_engine, text

from .api import create_app
from .completion.artifacts import ArtifactReservations
from .completion.coordinator import CompletionCoordinator
from .delivery.model import DeliveryPolicy
from .delivery.store import DeliveryStore
from .delivery.transport import DeliveryTargets, NotificationSink
from .delivery.worker import DeliveryWorker
from .inspection.cursors import CursorCodec
from .inspection.history import RuntimeHistory
from .lifecycle.access import RuntimeCredentials, RuntimePrincipal
from .lifecycle.admission import FixtureAdmission, FixtureCatalog


@dataclass(slots=True)
class Host:
    admission: FixtureAdmission
    credentials: RuntimeCredentials
    principals: tuple
    completion: CompletionCoordinator | None = None
    delivery: DeliveryWorker | None = None
    history: RuntimeHistory | None = None

    def app(self):
        return create_app(self.admission, self.credentials, self.completion, self.history)

    def close(self):
        self.admission.commands.engine.dispose()

    @classmethod
    def load(cls, path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not {"database_url_env", "principals", "fixtures"} <= set(raw) or set(raw) - {
            "database_url_env", "principals", "fixtures", "tools", "artifacts", "delivery", "inspection"}:
            raise ValueError("Explicit database, principals and fixture allowlist required")
        entries, principals = [], []
        for item in raw["principals"]:
            if set(item) != {"token_env", "actor_id", "scope", "actions"}:
                raise ValueError("Invalid principal configuration")
            actions = frozenset(item["actions"])
            if not actions or actions - {"admit", "claim", "renew", "cancel", "revoke", "maintain", "read", "complete", "outcome", "deliver", "inspect_receipts"}:
                raise ValueError("Invalid configured action")
            if not isinstance(item["actor_id"], str) or not item["actor_id"]:
                raise ValueError("Explicit actor required")
            principal = RuntimePrincipal(item["actor_id"], Scope.model_validate(item["scope"]), actions)
            principals.append(principal)
            entries.append((os.environ[item["token_env"]], principal))
        identities = {(p.actor_id, p.scope.tenant_id, p.scope.project_id) for p in principals}
        if len(identities) != len(principals):
            raise ValueError("Duplicate configured identity")
        credentials = RuntimeCredentials(entries)
        catalog = FixtureCatalog((AdmitFixtureRun.model_validate_json(json.dumps(d)) for d in raw["fixtures"]),
                                 (ToolDescriptor.model_validate_json(json.dumps(d)) for d in raw.get("tools", [])))
        artifacts = None
        if "artifacts" in raw:
            peer = raw["artifacts"]
            if set(peer) != {"runtime_owner", "reserve_endpoint", "token_env"}:
                raise ValueError("Invalid artifact peer configuration")
            artifacts = ArtifactReservations(peer["runtime_owner"], peer["reserve_endpoint"], os.environ[peer["token_env"]])
        delivery_config = raw.get("delivery", {})
        if set(delivery_config) - {"max_attempts", "lease_seconds", "notifications"}:
            raise ValueError("Unknown delivery configuration")
        policy = DeliveryPolicy(delivery_config.get("max_attempts", 8), delivery_config.get("lease_seconds", 30))
        notifications = {name: NotificationSink(item["endpoint"], os.environ[item["token_env"]])
                         for name, item in delivery_config.get("notifications", {}).items()}
        targets = DeliveryTargets(artifacts, notifications)
        cursors = None
        if "inspection" in raw:
            inspection = raw["inspection"]
            if set(inspection) - {"cursor_key_env", "ttl_seconds"}:
                raise ValueError("Unknown inspection configuration")
            cursors = CursorCodec(os.environ[inspection["cursor_key_env"]], ttl_seconds=inspection.get("ttl_seconds", 900))
        engine = create_engine(os.environ[raw["database_url_env"]], pool_pre_ping=True,
                               connect_args={"options": "-c statement_timeout=5000"})
        try:
            with engine.connect() as conn:
                if conn.execute(text("SELECT current_user")).scalar_one() != "runtime_service":
                    raise ValueError("Runtime service role required")
                conn.execute(text("SELECT deadline FROM runtime.attempts LIMIT 0"))
                conn.execute(text("SELECT operation_id FROM runtime.policy_outbox LIMIT 0"))
                conn.execute(text("SELECT tool_snapshot FROM runtime.runs LIMIT 0"))
                conn.execute(text("SELECT report_id FROM runtime.attempt_reports LIMIT 0"))
                conn.execute(text("SELECT delivery_token FROM runtime.outbox LIMIT 0"))
            completion = None if artifacts is None else CompletionCoordinator(engine, artifacts)
            return cls(FixtureAdmission(engine, catalog), credentials, tuple(principals), completion,
                       DeliveryWorker(DeliveryStore(engine, policy), targets),
                       None if cursors is None else RuntimeHistory(engine, cursors))
        except BaseException:
            engine.dispose()
            raise
