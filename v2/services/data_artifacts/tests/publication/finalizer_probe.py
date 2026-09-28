"""Explicit test-only process fault barriers; no production hook configuration."""

import json
import sys
from pathlib import Path

from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import Scope
from amphora_data_artifacts.publication.finalize import Finalizer
from amphora_data_artifacts.publication.model import ContentPolicy, Principal, UploadLimits
from amphora_data_artifacts.publication.uploads import Uploads
from amphora_data_artifacts.storage.local import LocalBytes
from sqlalchemy import create_engine

if __name__ == "__main__":
    config = json.loads(sys.stdin.readline())
    engine = create_engine(config["url"])
    try:
        principal = Principal("worker", Scope.model_validate(config["scope"]), frozenset({"upload", "finalize"}))
        policy = ContentPolicy(frozenset(tuple(entry) for entry in config["allowed"]))
        uploads = Uploads(engine, UploadLimits(**config["limits"]), policy)
        storage = LocalBytes(Path(config["root"]))
        original = storage.verify

        def paused_verify(key, descriptor):
            payload = original(key, descriptor)
            print("verified", flush=True)
            sys.stdin.readline()
            return payload

        if config["barrier"] == "verified":
            storage.verify = paused_verify
        Finalizer(uploads, storage).finalize(principal, parse_command("artifacts.finalize", config["command"]))
        print("committed", flush=True)
        sys.stdin.readline()  # Parent kills process before a client result is delivered.
    finally:
        engine.dispose()
