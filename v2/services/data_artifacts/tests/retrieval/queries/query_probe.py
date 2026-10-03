"""Fresh isolated Data query/replay process; emits safe results or bounded owner codes."""

import importlib.metadata
import importlib.util
import json
import os
import sys
from pathlib import Path

from amphora_contracts_core import Scope
from amphora_contracts_representations import RetrieveRepresentations
from amphora_data_artifacts.publication.model import Principal
from amphora_data_artifacts.reads import ArtifactReads
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.qdrant.transport import QdrantError
from amphora_data_artifacts.retrieval.queries.broker import RetrievalBroker
from amphora_data_artifacts.retrieval.validation import RetrievalError
from amphora_data_artifacts.source_rights.model import RightsError
from amphora_data_artifacts.storage.local import LocalBytes
from sqlalchemy import create_engine


def main():
    for module in ("amphora_research", "amphora_knowledge", "amphora_campaign_runtime"):
        assert importlib.util.find_spec(module) is None, "Independent Data owner required"
    handoff = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    engine = create_engine(os.environ["AMPHORA_QUERY_DATABASE_URL"])
    principal = Principal(handoff["actor_id"], Scope.model_validate(handoff["scope"]), frozenset(handoff["actions"]))
    reads = ArtifactReads(engine, LocalBytes(Path(handoff["storage"])), 65536)
    backend = QdrantAdapter(QdrantConfiguration(handoff["endpoint"], os.environ["AMPHORA_QUERY_API_KEY"]))
    broker = RetrievalBroker(reads, backend)
    request = RetrieveRepresentations.model_validate_json(json.dumps(handoff["request"]))
    output = {"pid": os.getpid(), "package": importlib.metadata.version("amphora-data-artifacts")}
    try:
        if handoff["mode"] == "read":
            value = broker.read(principal, request.retrieval_id)
        else:
            assert handoff["mode"] == "retrieve"
            value = broker.retrieve(principal, request)
        output["record"] = value.model_dump(mode="json")
    except (QdrantError, RightsError, RetrievalError) as error:
        output["error"] = str(error)
    finally:
        engine.dispose()
    print(json.dumps(output, separators=(",", ":")))


if __name__ == "__main__":
    main()
