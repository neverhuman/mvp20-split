"""Explicit local service configuration and startup; no migration side effects."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from amphora_contracts_core import Scope
from sqlalchemy import create_engine, text

from .access import Credentials
from .acquisition.ledger import AcquisitionLedger
from .acquisition.profiles import PreparedContentRule
from .acquisition.provenance import MAX_PROVENANCE_BYTES
from .acquisition.research import ResearchClient
from .acquisition.workflow import AcquisitionWorkflow
from .api import create_app
from .publication.model import ContentPolicy, Principal, UploadLimits
from .publication.schemas import configured_profiles
from .publication.uploads import Uploads
from .reads import ArtifactReads
from .representations.hosting import content_policy as representation_policy
from .representations.hosting import probe as representation_probe
from .representations.service import RepresentationService
from .retention.outcomes import RuntimeOutcomes
from .retrieval.hosting import configuration as retrieval_configuration
from .retrieval.hosting import probe as retrieval_probe
from .retrieval.qdrant.adapter import QdrantAdapter
from .retrieval.qdrant.configuration import QdrantConfiguration
from .retrieval.service import RetrievalService
from .storage.local import LocalBytes


@dataclass(slots=True)
class Host:
    uploads: Uploads
    storage: LocalBytes
    credentials: Credentials
    principals: tuple
    outcomes: RuntimeOutcomes | None
    acquisition_enabled: bool = False
    research: ResearchClient | None = None
    representations_enabled: bool = False
    retrieval_configuration: QdrantConfiguration | None = None

    def app(self):
        acquisition = representations = retrieval = None
        if self.acquisition_enabled or self.representations_enabled or self.retrieval_configuration is not None:
            engine = self.uploads.commands.engine
            reads = ArtifactReads(engine, self.storage, min(self.uploads.limits.max_bytes, MAX_PROVENANCE_BYTES))
            if self.acquisition_enabled:
                acquisition = AcquisitionWorkflow(reads, AcquisitionLedger(engine), self.research)
            if self.representations_enabled:
                representations = RepresentationService(reads, self.uploads, self.storage)
            if self.retrieval_configuration is not None:
                retrieval = RetrievalService(reads, QdrantAdapter(self.retrieval_configuration))
        return create_app(self.uploads, self.storage, self.credentials, self.outcomes,
                          acquisition=acquisition, representations=representations, retrieval=retrieval)

    def close(self):
        self.uploads.commands.engine.dispose()

    @classmethod
    def load(cls, path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if set(raw) - {"database_url_env", "storage_root", "principals", "profiles", "limits", "runtime", "acquisition", "research", "representations", "retrieval"}:
            raise ValueError("Unknown configuration field")
        acquisition = raw.get("acquisition", False)
        if type(acquisition) is not bool:
            raise ValueError("Acquisition flag must be boolean")
        representations = raw.get("representations", False)
        if type(representations) is not bool:
            raise ValueError("Representations flag must be boolean")
        retrieval = retrieval_configuration(raw["retrieval"]) if "retrieval" in raw else None
        research = None
        if "research" in raw:
            peer = raw["research"]
            if not acquisition or set(peer) != {"endpoint", "token_env"}:
                raise ValueError("Research peer requires enabled acquisition and explicit endpoint/token_env")
            research = ResearchClient(peer["endpoint"], os.environ[peer["token_env"]])
        storage = LocalBytes(Path(raw["storage_root"]))
        principals, entries = [], []
        for item in raw["principals"]:
            if set(item) != {"token_env", "actor_id", "scope", "actions"}:
                raise ValueError("Invalid principal configuration")
            actions = frozenset(item["actions"])
            if not actions or actions - {"upload", "finalize", "read", "retention", "cleanup", "acquire", "source_history", "manage_source_rights", "representation_manage", "representation_read", "representation_encode"}:
                raise ValueError("Invalid principal actions")
            principal = Principal(item["actor_id"], Scope.model_validate(item["scope"]), actions)
            principals.append(principal)
            entries.append((os.environ[item["token_env"]], principal))
        if not entries:
            raise ValueError("Explicit principals required")
        credentials = Credentials(entries)
        policy = ContentPolicy(*configured_profiles(raw["profiles"], Path(path).parent))
        if not policy.allowed:
            raise ValueError("Explicit profiles required")
        if acquisition:
            rules = (PreparedContentRule("document"), PreparedContentRule("lab"))
            policy = ContentPolicy(policy.allowed | frozenset(rule.identity for rule in rules), policy.rules + rules)
        if representations:
            policy = representation_policy(policy)
        limits = UploadLimits(**raw.get("limits", {}))
        outcomes = None
        if "runtime" in raw:
            runtime = raw["runtime"]
            outcomes = RuntimeOutcomes(runtime["owner"], runtime["endpoint"], os.environ[runtime["token_env"]])
        engine = create_engine(os.environ[raw["database_url_env"]], pool_pre_ping=True,
                               connect_args={"options": "-c statement_timeout=5000"})
        try:
            with engine.connect() as conn:
                if conn.execute(text("SELECT current_user")).scalar_one() != "artifact_service":
                    raise ValueError("Artifact service role required")
                conn.execute(text("SELECT created_at FROM artifacts.uploads LIMIT 0"))
                conn.execute(text("SELECT revision FROM artifacts.source_rights_heads LIMIT 0"))
                conn.execute(text("SELECT created_at FROM artifacts.derived_uploads LIMIT 0"))
                if representations:
                    representation_probe(conn)
                if retrieval is not None:
                    retrieval_probe(conn)
                if acquisition:
                    conn.execute(text("SELECT canonical_bytes FROM artifacts.source_revisions LIMIT 0"))
                    conn.execute(text("SELECT canonical_bytes FROM artifacts.conversion_traces LIMIT 0"))
                    conn.execute(text("SELECT canonical_bytes FROM artifacts.identity_observation_intents LIMIT 0"))
                    conn.execute(text("SELECT canonical_bytes FROM artifacts.identity_observation_results LIMIT 0"))
            return cls(Uploads(engine, limits, policy), storage, credentials, tuple(principals), outcomes,
                       acquisition_enabled=acquisition, research=research, representations_enabled=representations,
                       retrieval_configuration=retrieval)
        except BaseException:
            engine.dispose()
            raise
