"""Explicit local owner composition; startup never migrates or contacts peers."""

import json
import os
import re
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_knowledge import DomainVocabulary, ReasoningRuleSet
from amphora_tool_protocol import HttpTransport
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from ..access import Principal
from ..authoring.policy import StructuralPolicy
from ..authoring.vocabulary import Vocabulary
from ..persistence.ledger import KnowledgeLedger
from ..publication.identity import PublisherIdentity
from ..publication.store import PublicationStore
from ..publication.workflow import PublicationWorkflow
from ..reasoning.profile import RuleProfile
from ..reasoning.store import ReasoningStore
from ..reasoning.workflow import ReasoningWorkflow
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
        required = ("database_url_env", "principals", "vocabulary", "policy", "data", "research")
        keys(config, required + tuple(key for key in ("reasoning", "publication") if key in config))
        publisher, publication_transport = None, None
        if "publication" in config:
            publication = config["publication"]
            keys(publication, ("actor_id", "issuer_id", "token_env"))
            keys(config["data"], ("endpoint", "token_env"))
            publisher = PublisherIdentity(publication["actor_id"], publication["issuer_id"])
            publication_transport = HttpTransport(config["data"]["endpoint"], secret(publication["token_env"]))
        profiles = config.get("reasoning")
        if "reasoning" in config:
            if not isinstance(profiles, list) or len(profiles) > 32:
                raise ValueError("invalid_reasoning_configuration")
            profiles = tuple(RuleProfile(ReasoningRuleSet.model_validate_json(json.dumps(profile))) for profile in profiles)
        entries = config["principals"]
        if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
            raise ValueError("invalid_principals")
        grants = []
        for entry in entries:
            keys(entry, ("token_env", "actor_id", "scope", "actions"))
            actions = entry["actions"]
            if (not isinstance(actions, list) or not actions
                    or any(action not in ("read_graph", "propose_graph", "rebuild_graph", "reason_graph", "publish_reasoning") for action in actions)
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
                connection.execute(text("SELECT candidate_id FROM knowledge.snapshot_publications LIMIT 0"))
                if profiles is not None:
                    connection.execute(text("SELECT request_id FROM knowledge.reasoning_intents LIMIT 0"))
                if publisher is not None:
                    connection.execute(text("SELECT publication_id FROM knowledge.publication_terminals LIMIT 0"))
            workflow = AuthoringWorkflow(KnowledgeLedger(engine, vocabulary, policy), reviewer)
            reasoning = None if profiles is None else ReasoningWorkflow(ReasoningStore(engine), profiles, reviewer)
            publication = (None if publisher is None else
                PublicationWorkflow(PublicationStore(engine), reviewer, publisher, publication_transport))
            return cls(engine, create_app(workflow, credentials, reasoning, publication))
        except Exception:
            engine.dispose()
            raise

    def close(self):
        self.engine.dispose()
