"""Exercise installed executable over loopback; secrets arrive only via environment."""

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def main():
    with tempfile.TemporaryDirectory(prefix="amphora-artifact-acceptance-") as directory:
        root = Path(directory)
        storage = root / "bytes"
        storage.mkdir()
        scope = {"tenant_id": "acceptance", "project_id": uuid.uuid4().hex}
        profile_hash = hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()
        config = {"database_url_env": "AMPHORA_PROBE_DATABASE_URL", "storage_root": str(storage),
            "principals": [{"token_env": "AMPHORA_PROBE_TOKEN", "actor_id": "worker", "scope": scope,
                            "actions": ["upload", "finalize", "read", "cleanup"]},
                           {"token_env": "AMPHORA_PROBE_OTHER_TOKEN", "actor_id": "other",
                            "scope": {**scope, "project_id": "other"}, "actions": ["read"]}],
            "profiles": [{"media_type": "application/octet-stream", "schema_id": "fixture.bytes",
                          "version": "1", "sha256": profile_hash}]}
        config_path = root / "host.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        env = dict(os.environ, AMPHORA_PROBE_TOKEN=uuid.uuid4().hex, AMPHORA_PROBE_OTHER_TOKEN=uuid.uuid4().hex)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        child = subprocess.Popen([sys.executable, "-I", "-m", "amphora_data_artifacts", "serve",
            "--config", str(config_path), "--port", str(port)], env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        opener = build_opener(ProxyHandler({}))

        def request(path, method="GET", data=None, token=None):
            headers = {"Authorization": "Bearer " + (token or env["AMPHORA_PROBE_TOKEN"])}
            body = data if isinstance(data, bytes) else json.dumps(data).encode() if data is not None else None
            try:
                with opener.open(Request(f"http://127.0.0.1:{port}" + path, data=body,
                                         headers=headers, method=method), timeout=5) as response:
                    return response.status, response.read()
            except HTTPError as error:
                return error.code, error.read()

        def command(family, payload):
            return {"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
                                 "actor_id": "worker", "scope": scope}, "payload": payload}

        try:
            deadline = time.monotonic() + 30
            while True:
                try:
                    if request("/ready")[0] == 200:
                        break
                except URLError:
                    pass
                if child.poll() is not None or time.monotonic() >= deadline:
                    raise AssertionError("Installed artifact service did not become ready")
                time.sleep(0.1)
            content = {"sha256": hashlib.sha256(b"data").hexdigest(), "size_bytes": 4,
                       "media_type": "application/octet-stream", "schema_ref": {
                           "schema_id": "fixture.bytes", "version": "1", "sha256": profile_hash}}
            status, body = request("/v1/uploads", "POST", command("artifacts.begin_upload", {"content": content}))
            assert status == 200
            upload_id = json.loads(body)["upload_id"]
            assert request(f"/v1/uploads/{upload_id}/content", "PUT", b"data")[0] == 200
            finalized = command("artifacts.finalize", {"upload_id": upload_id, "content": content})
            status, body = request("/v1/artifacts/finalize", "POST", finalized)
            assert status == 200
            artifact = json.loads(body)["artifact"]
            assert json.loads(request("/v1/artifacts/finalize", "POST", finalized)[1])["artifact"] == artifact
            path = "/v1/artifacts/" + artifact["artifact_id"]
            assert json.loads(request(path)[1]) == artifact
            assert request(path + "/content") == (200, b"data")
            assert request(path, token="invalid")[0] == 401
            assert request(path, token=env["AMPHORA_PROBE_OTHER_TOKEN"])[0] == 404
            payload_path = next(p for p in storage.iterdir() if len(p.name) == 32)
            payload_path.write_bytes(b"oops")  # Fixture-only integrity fault; never a production write API.
            assert request(path + "/content")[0] == 409
        finally:
            child.terminate()
            try:
                child.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.communicate(timeout=10)
        print("Installed artifact executable: publish/replay/scoped reads/integrity checks passed")


if __name__ == "__main__":
    main()
