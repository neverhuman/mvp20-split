"""Explicit labeled local Qdrant fixture; retains all state on stop/restart."""

import argparse
import json
import secrets
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
STATE = ROOT / ".test-results/qdrant-fixture.json"
IMAGE = "qdrant/qdrant@sha256:12364fe851b9f17356fc88189fc06d1b521262e04659ec7345975b00c9246a10"
VERSION = "1.19.1"
LABEL = "amphora.qdrant-fixture"


def docker(*args):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError("Qdrant fixture Docker operation failed: " + args[0])
    return result.stdout.strip()


def owned_state():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state["image"] != IMAGE:
        raise RuntimeError("Fixture image identity mismatch")
    for kind, name in (("container", state["container"]), ("volume", state["volume"])):
        obj = json.loads(docker(kind, "inspect", name))[0]
        labels = obj["Config"].get("Labels", {}) if kind == "container" else obj.get("Labels", {})
        if labels.get(LABEL) != state["owner"]:
            raise RuntimeError("Fixture ownership mismatch")
        if kind == "container" and obj["Config"]["Image"] != IMAGE:
            raise RuntimeError("Fixture running image mismatch")
    return state


def endpoint(state):
    address = docker("port", state["container"], "6333/tcp")
    if not address.startswith("127.0.0.1:") or "\n" in address:
        raise RuntimeError("Fixture port must bind loopback only")
    port = int(address.split(":")[1])
    if not 1 <= port <= 65535:
        raise RuntimeError("Fixture port invalid")
    return "http://127.0.0.1:" + str(port)


def server(url, token, path="/"):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url + path, headers={"api-key": token})
    with opener.open(request, timeout=2) as response:
        raw = response.read(8193)
    if len(raw) > 8192:
        raise RuntimeError("Fixture readiness response bound")
    return json.loads(raw)


def verify():
    state = owned_state()
    state["endpoint"] = endpoint(state)
    deadline = time.monotonic() + 30
    while True:
        try:
            result = server(state["endpoint"], state["api_key"])
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                raise RuntimeError("Qdrant fixture readiness deadline") from None
            time.sleep(0.2)
    if result.get("version") != VERSION:
        raise RuntimeError("Qdrant fixture version mismatch")
    # Root version metadata is intentionally public in Qdrant; verify a protected route.
    protected = "/collections/amphora_" + "0" * 64
    try:
        server(state["endpoint"], state["api_key"], protected)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise RuntimeError("Authenticated collection probe failed") from None
    try:
        server(state["endpoint"], "wrong-fixture-key-" + "x" * 32, protected)
    except urllib.error.HTTPError as error:
        if error.code not in (401, 403):
            raise RuntimeError("Unexpected authentication response") from None
    else:
        raise RuntimeError("Qdrant fixture did not enforce API-key authentication")
    state["server_version"] = result["version"]
    state["commit"] = result.get("commit")
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print("Pinned Qdrant fixture authenticated and ready; " + state["endpoint"])


def start():
    if STATE.exists():
        raise RuntimeError("Fixture state already exists; inspect or resume it")
    owner = uuid.uuid4().hex
    name = "amphora-bp06-qdrant-" + owner
    state = {
        "owner": owner,
        "container": name,
        "volume": name + "-data",
        "image": IMAGE,
        "api_key": secrets.token_hex(32),
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    docker("volume", "create", "--label", LABEL + "=" + owner, state["volume"])
    docker(
        "run",
        "--detach",
        "--name",
        name,
        "--label",
        LABEL + "=" + owner,
        "--restart",
        "no",
        "-p",
        "127.0.0.1::6333",
        "--mount",
        "type=volume,source=" + state["volume"] + ",target=/qdrant/storage",
        "-e",
        "QDRANT__SERVICE__API_KEY=" + state["api_key"],
        "-e",
        "QDRANT__TELEMETRY_DISABLED=true",
        IMAGE,
    )
    verify()


def stop():
    state = owned_state()
    docker("stop", state["container"])
    print("Qdrant fixture stopped; owned volume and state retained")


def resume():
    state = owned_state()
    docker("start", state["container"])
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "verify", "stop", "resume"))
    action = parser.parse_args().action
    {"start": start, "verify": verify, "stop": stop, "resume": resume}[action]()
