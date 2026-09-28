"""Explicit local fixture host; startup validates ownership and never migrates."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from amphora_contracts_core import Scope
from amphora_contracts_runtime import AdmitFixtureRun
from sqlalchemy import create_engine, text

from .api import create_app
from .lifecycle.access import RuntimeCredentials, RuntimePrincipal
from .lifecycle.admission import FixtureAdmission, FixtureCatalog


@dataclass(slots=True)
class Host:
    admission: FixtureAdmission
    credentials: RuntimeCredentials
    principals: tuple

    def app(self):
        return create_app(self.admission, self.credentials)

    def close(self):
        self.admission.commands.engine.dispose()

    @classmethod
    def load(cls, path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if set(raw) != {"database_url_env", "principals", "fixtures"}:
            raise ValueError("Explicit database, principals and fixture allowlist required")
        entries, principals = [], []
        for item in raw["principals"]:
            if set(item) != {"token_env", "actor_id", "scope", "actions"}:
                raise ValueError("Invalid principal configuration")
            actions = frozenset(item["actions"])
            if not actions or actions - {"admit", "claim", "renew", "cancel", "revoke", "maintain", "read"}:
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
        catalog = FixtureCatalog(AdmitFixtureRun.model_validate_json(json.dumps(d)) for d in raw["fixtures"])
        engine = create_engine(os.environ[raw["database_url_env"]], pool_pre_ping=True,
                               connect_args={"options": "-c statement_timeout=5000"})
        try:
            with engine.connect() as conn:
                if conn.execute(text("SELECT current_user")).scalar_one() != "runtime_service":
                    raise ValueError("Runtime service role required")
                conn.execute(text("SELECT deadline FROM runtime.attempts LIMIT 0"))
                conn.execute(text("SELECT operation_id FROM runtime.policy_outbox LIMIT 0"))
            return cls(FixtureAdmission(engine, catalog), credentials, tuple(principals))
        except BaseException:
            engine.dispose()
            raise
