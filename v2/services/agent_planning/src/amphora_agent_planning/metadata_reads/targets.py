"""Closed GET targets; untrusted text cannot choose an owner route or result type."""

import re
from urllib.parse import parse_qsl, urlsplit

from amphora_contracts_graph_runtime import DefinitionSchema, DefinitionUniverse
from amphora_contracts_representations import RetrievalRecord
from amphora_contracts_tools import ReleasePage, ReleaseSnapshot

from ..context.policy import require

DIGEST = r"[0-9a-f]{64}"
IDENTIFIER = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}"
RELEASE = r"[0-9]+\.[0-9]+\.[0-9]+"


def matches(pattern, value):
    return type(value) is str and re.fullmatch(pattern, value) is not None


def target(owner, path):
    require(type(path) is str and len(path) <= 2048 and all(33 <= ord(char) <= 126 for char in path), "metadata_path")
    parsed = urlsplit(path)
    require(not parsed.scheme and not parsed.netloc and not parsed.fragment, "metadata_path")
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    query = dict(pairs)
    require(len(query) == len(pairs), "metadata_query")
    if owner == "registry" and parsed.path == "/v1/releases":
        require(set(query) <= {"limit", "after", "capability_id", "release"} and "limit" in query, "metadata_query")
        require(matches(r"[1-9][0-9]{0,2}", query["limit"]) and int(query["limit"]) <= 100, "metadata_query")
        for name, pattern in (("after", DIGEST), ("capability_id", IDENTIFIER), ("release", RELEASE)):
            require(name not in query or (len(query[name]) <= 128 and matches(pattern, query[name])), "metadata_query")
        return ReleasePage
    if owner == "registry" and matches(r"/v1/releases/" + DIGEST, parsed.path):
        require(not query and not parsed.query, "metadata_query")
        return ReleaseSnapshot
    if owner == "runtime" and parsed.path == "/v1/definition-universe":
        require(not query and not parsed.query, "metadata_query")
        return DefinitionUniverse
    if owner == "runtime" and matches(r"/v1/definition-schemas/" + DIGEST, parsed.path):
        require(set(query) == {"schema_id", "version", "universe_sha256"} and query["version"] == "1" and
                matches(IDENTIFIER, query["schema_id"]) and matches(DIGEST, query["universe_sha256"]), "metadata_query")
        return DefinitionSchema
    if owner == "data" and matches(r"/v1/retrieval/queries/" + IDENTIFIER, parsed.path):
        require(not query and not parsed.query, "metadata_query")
        return RetrievalRecord
    raise ValueError("metadata_path")
