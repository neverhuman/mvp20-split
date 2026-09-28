"""Test-only crash barriers for cleanup and a live writer."""

import json
import sys
from pathlib import Path

from amphora_contracts_core import Scope
from amphora_data_artifacts.maintenance.cleanup import Cleanup
from amphora_data_artifacts.publication.model import ContentPolicy, Principal, UploadLimits
from amphora_data_artifacts.publication.uploads import Uploads
from amphora_data_artifacts.storage.local import LocalBytes
from sqlalchemy import create_engine

if __name__ == "__main__":
    config = json.loads(sys.stdin.readline())
    engine = create_engine(config["url"])
    principal = Principal("worker", Scope.model_validate(config["scope"]), frozenset({"upload", "cleanup"}))
    uploads = Uploads(engine, UploadLimits(**config["limits"]),
                      ContentPolicy(frozenset(tuple(x) for x in config["allowed"])))
    storage = LocalBytes(Path(config["root"]))
    if config["mode"] == "writer":
        attempt = uploads.start(principal, config["upload"])
        writer = storage.writer(attempt)
        writer.write(b"da")
        print("writer", flush=True)
        sys.stdin.readline()
    else:
        original = storage.retire

        def paused(key):
            if config["mode"] == "retired":
                original(key)
            print(config["mode"], flush=True)
            sys.stdin.readline()

        storage.retire = paused
        Cleanup(uploads, storage).sweep(principal)
