"""Explicit optional backend configuration and SQL-only readiness; no migrations."""

import os
import re

from sqlalchemy import text

from ..representations.hosting import probe as representation_probe
from .qdrant.configuration import QdrantConfiguration


def configuration(value):
    if (
        type(value) is not dict
        or not {"endpoint", "token_env"} <= value.keys()
        or value.keys() - {"endpoint", "token_env", "timeout"}
    ):
        raise ValueError("Retrieval requires explicit endpoint/token_env and optional timeout")
    name = value["token_env"]
    if type(name) is not str or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", name):
        raise ValueError("Retrieval token environment name required")
    return QdrantConfiguration(value["endpoint"], os.environ[name], value.get("timeout", 5.0))


def probe(connection):
    representation_probe(connection)
    for table in (
        "index_generations",
        "index_generation_bindings",
        "index_build_attempts",
        "index_generation_events",
        "index_generation_cursors",
        "index_verifications",
        "index_publications",
        "index_heads",
        "retrieval_queries",
        "retrieval_results",
    ):
        connection.execute(text("SELECT tenant_id FROM artifacts." + table + " LIMIT 0"))
