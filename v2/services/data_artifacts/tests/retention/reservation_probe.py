"""Test-only transaction crash barriers; authentication has separate HTTP probes."""

import json
import sys
from types import SimpleNamespace

from amphora_contracts_artifacts import RuntimeOutcome, parse_command
from amphora_contracts_core import Scope
from amphora_data_artifacts.publication.model import ContentPolicy, Principal, UploadLimits
from amphora_data_artifacts.publication.uploads import Uploads
from amphora_data_artifacts.retention.reservations import Reservations
from sqlalchemy import create_engine, event

if __name__ == "__main__":
    config = json.loads(sys.stdin.readline())
    engine = create_engine(config["url"])
    principal = Principal("worker", Scope.model_validate(config["scope"]), frozenset({"retention"}))
    uploads = Uploads(engine, UploadLimits(), ContentPolicy(frozenset()))
    peer = SimpleNamespace(lookup=lambda binding: RuntimeOutcome.model_validate({
        "binding": binding.model_dump(), "proof": config["proof"]}))

    def pause(_conn, _cursor, statement, *_args):
        if statement.startswith("UPDATE artifacts.reservations SET status="):
            print("transition", flush=True)
            sys.stdin.readline()

    if config["barrier"] == "transition":
        event.listen(engine, "after_cursor_execute", pause)
    Reservations(uploads, peer).reconcile(principal, parse_command("artifacts.reconcile", config["command"]))
    print("committed", flush=True)
    sys.stdin.readline()
