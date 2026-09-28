import asyncio
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from sqlalchemy import text
from starlette.requests import ClientDisconnect

pytestmark = pytest.mark.postgres


def capacity(env):
    with env.engine.connect() as conn:
        return conn.execute(text("SELECT * FROM artifacts.capacity WHERE tenant_id=:tenant AND project_id=:project"),
                            env.principal.bindings).mappings().one()


@pytest.mark.parametrize("failure", ["disconnect", "cancel", "timeout"])
def test_interrupted_request_remains_provisional(upload_env, failure):
    e = upload_env
    e.uploads.limits = replace(e.uploads.limits, seconds=1)
    upload_id = e.begin().upload_id

    async def exercise():
        received = False
        messages = []

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": b"da", "more_body": True}
            if failure == "disconnect":
                return {"type": "http.disconnect"}
            if failure == "cancel":
                raise asyncio.CancelledError()
            await asyncio.sleep(5)
            raise AssertionError("Timeout should interrupt")

        async def send(message):
            messages.append(message)

        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "PUT", "scheme": "http", "path": f"/v1/uploads/{upload_id}/content",
            "query_string": b"", "root_path": "", "server": ("test", 80), "client": ("local", 1),
            "headers": [(b"authorization", ("Bearer " + "a" * 32).encode())]}
        if failure == "timeout":
            await e.client.app(scope, receive, send)
            assert messages[0]["status"] == 409
        else:
            expected = ClientDisconnect if failure == "disconnect" else asyncio.CancelledError
            with pytest.raises(expected):
                await e.client.app(scope, receive, send)

    asyncio.run(exercise())
    assert capacity(e)["active_streams"] == 0
    assert capacity(e)["charged_bytes"] == 2
    with e.engine.connect() as conn:
        row = conn.execute(text("SELECT status,selected_attempt FROM artifacts.uploads WHERE tenant_id=:tenant "
                                "AND project_id=:project"), e.principal.bindings).one()
        assert tuple(row) == ("provisional", None)


def test_two_process_writers_new_generation_wins(upload_env):
    e = upload_env
    upload_id = e.begin().upload_id
    config = {"url": e.engine.url.render_as_string(hide_password=False), "scope": e.principal.scope.model_dump(),
              "upload_id": upload_id, "root": str(e.storage.root), "limits": asdict(e.uploads.limits)}
    workers = []
    records = []
    try:
        for _ in range(2):
            worker = subprocess.Popen([sys.executable, "-I", str(Path(__file__).with_name("worker_probe.py"))],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            workers.append(worker)
            worker.stdin.write(json.dumps(config) + "\n")
            worker.stdin.flush()
            with ThreadPoolExecutor(1) as pool:
                try:
                    line = pool.submit(worker.stdout.readline).result(timeout=15)
                except TimeoutError:
                    worker.kill()
                    raise
            assert line, "Worker did not reach write barrier"
            records.append(json.loads(line))
        for worker, expected in [(workers[1], "streamed"), (workers[0], "stale")]:
            output, _ = worker.communicate("finish\n", timeout=15)
            assert worker.returncode == 0 and output.strip() == expected
        assert records[0]["key"] != records[1]["key"]
        assert all(e.storage.path(r["key"]).read_bytes() == b"data" for r in records)
        with e.engine.connect() as conn:
            assert conn.execute(text("SELECT selected_attempt FROM artifacts.uploads WHERE tenant_id=:tenant "
                "AND project_id=:project"), e.principal.bindings).scalar_one() == records[1]["attempt_id"]
        assert capacity(e)["active_streams"] == 0
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
            worker.wait(timeout=10)
