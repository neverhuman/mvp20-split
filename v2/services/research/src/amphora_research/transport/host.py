"""Explicit local read-only hosting configuration; secrets are environment references."""

import os
from dataclasses import dataclass

from amphora_contracts_core import Scope
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from ..persistence.ledger import IdentityLedger
from .access import Credentials, Principal
from .api import create_app
from .assessments import AssessmentOperations
from .resolver import IdentityResolver


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("invalid_host_configuration")


def _secret(name):
    if not isinstance(name, str) or not name or len(name) > 128:
        raise ValueError("invalid_environment_reference")
    value = os.environ.get(name)
    if not value:
        raise ValueError("missing_environment_reference")
    return value


@dataclass
class ResearchHost:
    engine: object
    app: object

    @classmethod
    def configured(cls, config):
        optional = ("assessment",) if isinstance(config, dict) and "assessment" in config else ()
        _keys(config, ("database_url_env", "principals", *optional))
        entries = config["principals"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
            raise ValueError("invalid_principals")
        grants = []
        for entry in entries:
            _keys(entry, ("token_env", "actor_id", "scope", "actions"))
            if not isinstance(entry["actor_id"], str) or not 1 <= len(entry["actor_id"]) <= 128:
                raise ValueError("invalid_actor")
            actions = entry["actions"]
            if (not isinstance(actions, list) or not actions
                    or any(action not in ("resolve_identity", "read_declarations", "assess", "read_assessment",
                                          "publish_assessment", "read_assessment_publication",
                                          "correct_assessment_receipt", "select_assessment_receipt") for action in actions)
                    or len(set(actions)) != len(actions)):
                raise ValueError("invalid_actions")
            scope = Scope.model_validate(entry["scope"])
            grants.append((_secret(entry["token_env"]), Principal(entry["actor_id"], scope, frozenset(entry["actions"]))))
        if not optional and any(principal.actions - {"resolve_identity", "read_declarations"} for _, principal in grants):
            raise ValueError("assessment_configuration_required")
        credentials = Credentials(grants)
        url = make_url(_secret(config["database_url_env"]))
        if url.drivername != "postgresql+psycopg" or url.username != "research_service":
            raise ValueError("research_service_role_required")
        engine = create_engine(url, pool_size=4, max_overflow=2, pool_timeout=2,
                               connect_args={"connect_timeout": 5, "options": "-c statement_timeout=5000"})
        try:
            with engine.connect() as connection:
                if connection.execute(text("SELECT current_user")).scalar_one() != "research_service":
                    raise ValueError("research_service_role_required")
                connection.execute(text("SELECT revision FROM research.identity_heads LIMIT 1"))
            assessments = None
            if optional:
                assessment = config["assessment"]
                _keys(assessment, ("profiles", "data", "publication"))
                _keys(assessment["data"], ("endpoint", "token_env"))
                _keys(assessment["publication"], ("actor_id", "issuer_id", "token_env"))
                publisher = assessment["publication"]
                assessments = AssessmentOperations(engine, assessment["profiles"], assessment["data"]["endpoint"],
                    _secret(assessment["data"]["token_env"]), publisher["actor_id"], publisher["issuer_id"],
                    _secret(publisher["token_env"]))
                with engine.connect() as connection:
                    connection.execute(text("SELECT canonical_bytes FROM research.assessment_decisions LIMIT 1"))
                    connection.execute(text("SELECT position FROM research.publication_events LIMIT 1"))
                    connection.execute(text("SELECT ordinal FROM research.receipt_corrections LIMIT 1"))
            return cls(engine, create_app(IdentityResolver(IdentityLedger(engine)), credentials, assessments))
        except Exception:
            engine.dispose()
            raise

    def close(self):
        self.engine.dispose()
