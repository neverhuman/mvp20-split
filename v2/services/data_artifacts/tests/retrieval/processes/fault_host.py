"""Explicit test-only installed HTTP fault host; never packaged or production selectable."""

import importlib.util
import json
import sys
import threading

import uvicorn
from amphora_data_artifacts.hosting import Host
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.publication import GenerationPublication
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.queries import broker
from sqlalchemy import event

STAGES = {
    "generation_intent",
    "projection_written",
    "verification_committed",
    "publication_committed",
    "query_intent",
    "query_observed",
    "query_before_result",
    "query_committed",
}


def barrier(stage, **metadata):
    print(json.dumps({"stage": stage, **metadata}), flush=True)
    released = threading.Event()

    def read():
        if sys.stdin.readline().strip() == "release":
            released.set()

    threading.Thread(target=read, daemon=True).start()
    if not released.wait(timeout=30):
        raise TimeoutError("Explicit retrieval test barrier not released")


def after(owner, name, stage, projection):
    original = getattr(owner, name)

    def wrapped(*args, **kwargs):
        result = original(*args, **kwargs)
        barrier(stage, **projection(result))
        return result

    setattr(owner, name, wrapped)


def main():
    assert all(
        importlib.util.find_spec(m) is None
        for m in ("amphora_research", "amphora_knowledge", "amphora_campaign_runtime")
    )
    request = json.loads(sys.stdin.readline())
    if set(request) != {"config", "port", "stage"} or request["stage"] not in STAGES:
        raise ValueError("Explicit retrieval test stage required")
    stage = request["stage"]
    host = Host.load(request["config"])
    if stage == "generation_intent":
        after(GenerationIntents, "prepare", stage, lambda value: {"status": value.model_dump(mode="json")})
    elif stage == "projection_written":
        after(QdrantAdapter, "build", stage, lambda _: {})
    elif stage == "verification_committed":
        after(GenerationPublication, "build_and_verify", stage, lambda value: {"proof": value.descriptor()})
    elif stage == "publication_committed":
        after(
            GenerationPublication, "publish", stage, lambda value: {"status": value.model_dump(mode="json")}
        )
    elif stage == "query_intent":
        original = broker.execute

        def before(*args, **kwargs):
            barrier(stage)
            return original(*args, **kwargs)

        broker.execute = before
    elif stage == "query_observed":
        after(QdrantAdapter, "query", stage, lambda value: {"scores": [item.score for item in value]})
    elif stage == "query_committed":
        after(
            broker.RetrievalBroker, "retrieve", stage, lambda value: {"record": value.model_dump(mode="json")}
        )
    else:

        def before_sql(_connection, _cursor, statement, parameters, _context, _many):
            if statement.startswith("INSERT INTO artifacts.retrieval_results "):
                barrier(stage, retrieval_id=parameters["retrieval"])

        event.listen(host.uploads.commands.engine, "before_cursor_execute", before_sql)
    try:
        uvicorn.run(host.app(), host="127.0.0.1", port=request["port"], access_log=False)
    finally:
        host.close()


if __name__ == "__main__":
    main()
