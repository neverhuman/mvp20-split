"""Explicit test-only ingestion host. Never packaged or selectable by production config."""

import asyncio
import json
import sys
import threading

import uvicorn
from amphora_data_artifacts.hosting import Host
from sqlalchemy import event


def barrier(payload):
    print(json.dumps(payload), flush=True)
    released = threading.Event()

    def read():
        if sys.stdin.readline().strip() == "release":
            released.set()

    threading.Thread(target=read, daemon=True).start()
    if not released.wait(timeout=30):
        raise TimeoutError("Explicit ingestion fault barrier was not released")


def main():
    request = json.loads(sys.stdin.readline())
    stages = {"source_before_head", "trace_committed", "observation_before_result", "observation_committed"}
    if set(request) != {"config", "port", "fault"} or request["fault"] not in stages:
        raise ValueError("Explicit ingestion fault required")
    host = Host.load(request["config"])
    stage = request["fault"]

    def before_sql(_conn, _cursor, statement, parameters, _context, _many):
        prefix = {"source_before_head": "INSERT INTO artifacts.source_heads ",
                  "observation_before_result": "INSERT INTO artifacts.identity_observation_results "}.get(stage)
        if prefix is not None and statement.startswith(prefix):
            barrier({"stage": stage, "source": parameters.get("source"), "observation": parameters.get("observation")})

    event.listen(host.uploads.commands.engine, "before_cursor_execute", before_sql)
    original = host.app()

    async def app(scope, receive, send):
        status = None
        body = bytearray()

        async def held_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            route = {"trace_committed": "/v1/acquisition/retain",
                     "observation_committed": "/v1/acquisition/identity-observations"}.get(stage)
            if message["type"] == "http.response.body" and scope.get("path") == route:
                body.extend(message.get("body", b""))
                if status == 200 and not message.get("more_body", False):
                    await asyncio.to_thread(barrier, {"stage": stage, "receipt": json.loads(body)})
            await send(message)

        await original(scope, receive, held_send)

    try:
        uvicorn.run(app, host="127.0.0.1", port=request["port"], access_log=False)
    finally:
        host.close()


if __name__ == "__main__":
    main()
