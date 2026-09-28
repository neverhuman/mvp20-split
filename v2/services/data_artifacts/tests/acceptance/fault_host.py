"""Explicit test-only artifact process. Not packaged or enabled by service config."""

import asyncio
import json
import sys
import threading

import uvicorn
from amphora_data_artifacts.hosting import Host


def barrier(event):
    print(json.dumps(event), flush=True)
    released = threading.Event()

    def read():
        if sys.stdin.readline().strip() == "release":
            released.set()

    threading.Thread(target=read, daemon=True).start()
    if not released.wait(timeout=30):
        raise TimeoutError("Explicit fault barrier was not released")


def main():
    config = json.loads(sys.stdin.readline())
    if set(config) != {"config", "port", "fault"} or config["fault"] not in {"upload_synced", "finalize_committed"}:
        raise ValueError("Explicit named test fault required")
    host = Host.load(config["config"])
    try:
        app = host.app()
        if config["fault"] == "upload_synced":
            original_writer = host.storage.writer

            def writer(attempt):
                result = original_writer(attempt)
                original_seal = result.seal

                def seal():
                    original_seal()
                    barrier({"barrier": "upload_synced", "upload_id": attempt.upload_id, "attempt_id": attempt.attempt_id})

                result.seal = seal
                return result

            host.storage.writer = writer
        else:
            original_app = app

            async def held_app(scope, receive, send):
                status = None
                body = bytearray()

                async def held_send(message):
                    nonlocal status
                    if message["type"] == "http.response.start":
                        status = message["status"]
                    if message["type"] == "http.response.body" and scope.get("path") == "/v1/artifacts/finalize":
                        body.extend(message.get("body", b""))
                        if status == 200 and not message.get("more_body", False):
                            await asyncio.to_thread(barrier, {"barrier": "finalize_committed", "receipt": json.loads(body)})
                    await send(message)

                await original_app(scope, receive, held_send)

            app = held_app
        uvicorn.run(app, host="127.0.0.1", port=config["port"], access_log=False)
    finally:
        host.close()


if __name__ == "__main__":
    main()
