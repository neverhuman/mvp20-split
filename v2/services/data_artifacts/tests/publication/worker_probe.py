"""Test-only independent writer; configuration/credentials arrive over stdin."""

import json
import sys

from amphora_contracts_core import Scope
from amphora_data_artifacts.publication.model import ContentPolicy, Principal, UploadLimits
from amphora_data_artifacts.publication.uploads import Uploads
from amphora_data_artifacts.storage.local import LocalBytes
from sqlalchemy import create_engine

if __name__ == "__main__":
    from pathlib import Path

    config = json.loads(sys.stdin.readline())
    engine = create_engine(config["url"])
    try:
        principal = Principal("worker", Scope.model_validate(config["scope"]), frozenset({"upload"}))
        uploads = Uploads(engine, UploadLimits(**config["limits"]), ContentPolicy(frozenset()))
        attempt = uploads.start(principal, config["upload_id"])
        writer = LocalBytes(Path(config["root"])).writer(attempt)
        print(json.dumps({"attempt_id": attempt.attempt_id, "key": attempt.storage_key}), flush=True)
        if sys.stdin.readline().strip() != "finish":
            raise ValueError("Expected test barrier release")
        writer.write(b"data")
        writer.seal()
        writer.close()
        status = uploads.finish(principal, attempt, verified=True, actual_bytes=4)
        print(status, flush=True)
    finally:
        engine.dispose()
