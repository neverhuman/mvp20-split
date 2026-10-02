"""Explicit local owner composition; startup never migrates or contacts peers."""

import json
import os
import re
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_knowledge import DomainVocabulary
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from ..access import Principal
from ..authoring.policy import StructuralPolicy
from ..authoring.vocabulary import Vocabulary
from ..persistence.ledger import KnowledgeLedger
from ..validation.peers import DataReader, ResearchReader
from ..validation.review import ReferenceReviewer
from ..validation.transport import PeerTransport
from ..validation.workflow import AuthoringWorkflow
from .api import create_app
from .credentials import Credentials


def keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError("invalid_host_configuration")


def secret(name):
    if not isinstance(name, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name) is None:
        raise ValueError("invalid_environment_reference")
    value = os.environ.get(name)
    if not value:
        raise ValueError("missing_environment_reference")
    return value


def peer(config):
    keys(config, ("endpoint", "token_env"))
    return PeerTransport(config["endpoint"], secret(config["token_env"]))


@dataclass
class KnowledgeHost:
    engine: object
    app: object

    @classmethod
    def configured(cls, config):
        keys(config, ("database_url_env", "principals", "vocabulary", "policy", "data", "research"))
        entries = config["principals"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
            raise ValueError("invalid_principals")
        grants = []
        for entry in entries:
            keys(entry, ("token_env", "actor_id", "scope", "actions"))
            actions = entry["actions"]
            if (not isinstance(actions, list) or not actions
                    or any(action not in ("read_graph", "propose_graph") for action in actions)
                    or len(set(actions)) != len(actions)):
                raise ValueError("invalid_actions")
            grants.append((secret(entry["token_env"]), Principal(entry["actor_id"],
                Scope.model_validate(entry["scope"]), frozenset(actions))))
        credentials = Credentials(grants)
        vocabulary = Vocabulary(DomainVocabulary.model_validate_json(json.dumps(config["vocabulary"])))
        policy = StructuralPolicy.from_definition(config["policy"])
        reviewer = ReferenceReviewer(DataReader(peer(config["data"])), ResearchReader(peer(config["research"])))
        url = make_url(secret(config["database_url_env"]))
        if url.drivername != "postgresql+psycopg" or url.username != "knowledge_service":
            raise ValueError("knowledge_service_role_required")
        engine = create_engine(url, pool_size=4, max_overflow=2, pool_timeout=2,
            connect_args={"connect_timeout": 5, "options": "-c statement_timeout=5000"})
        try:
            with engine.connect() as connection:
                if connection.execute(text("SELECT current_user")).scalar_one() != "knowledge_service":
                    raise ValueError("knowledge_service_role_required")
                connection.execute(text("SELECT revision FROM knowledge.heads LIMIT 1"))
            workflow = AuthoringWorkflow(KnowledgeLedger(engine, vocabulary, policy), reviewer)
            return cls(engine, create_app(workflow, credentials))
        except Exception:
            engine.dispose()
            raise

    def close(self):
        self.engine.dispose()
