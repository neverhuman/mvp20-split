"""Actual selected-local-host preflight; bounded owned storage and loopback probes."""

import argparse
import hashlib
import json
import os
import platform
import secrets
import socket
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def storage_probe(root, python):
    root.mkdir(parents=True, exist_ok=True)
    name = ".amphora-preflight-" + uuid.uuid4().hex
    original, replaced = root / (name + ".pending"), root / (name + ".retained")
    payload = b"amphora-local-storage-probe-v1\n" + secrets.token_bytes(128)
    try:
        with original.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(original, replaced)
        expected = hashlib.sha256(payload).hexdigest()
        script = "import hashlib,pathlib,sys; assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()==sys.argv[2]"
        subprocess.run([str(python), "-I", "-c", script, str(replaced), expected], check=True, capture_output=True, timeout=15)
        return {"status": "passed", "operations": ["exclusive_create", "write", "file_fsync", "same_directory_replace", "fresh_process_hash_read"],
                "sha256": expected, "scope": "normal_operation_only_not_power_loss_or_backup_proof"}
    finally:
        for path in (original, replaced):
            path.unlink(missing_ok=True)


def loopback_probe():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(5)
        with socket.create_connection(listener.getsockname(), timeout=5) as client:
            connection, peer = listener.accept()
            with connection:
                connection.settimeout(5)
                client.sendall(b"local-only")
                assert connection.recv(64) == b"local-only"
                assert listener.getsockname()[0] == peer[0] == "127.0.0.1"
        return {"status": "passed", "bind_host": "127.0.0.1", "scope": "temporary_socket_only_not_service_auth_or_firewall_proof"}


def verify(output, storage, installation, python):
    output, storage, installation = output.absolute(), storage.absolute(), installation.absolute()
    output.mkdir(parents=True, exist_ok=False)
    assert platform.system() == "Windows" and platform.machine().lower() in ("amd64", "x86_64")
    manifest = json.loads((installation / "manifest.json").read_bytes())
    assert manifest["status"] == "installed"
    artifacts = []
    for wheel, expected in manifest["wheels"].items():
        assert Path(wheel).name == wheel
        assert digest(installation / "wheels" / wheel) == expected
        name, release = wheel.split("-")[:2]
        artifacts.append({"name": name, "release": release, "sha256": expected, "operating_system": "windows", "architecture": "x86_64"})
    storage_evidence = storage_probe(storage, python)
    network_evidence = loopback_probe()
    profile = {"schema_version": "1", "profile_id": "local-windows-demo", "target": {
        "host_id": socket.gethostname(), "operating_system": "windows", "architecture": "x86_64", "python": "3.12",
        "min_cpu_count": 4, "min_memory_bytes": 8 * 1024**3, "accelerator": "none"},
        "storage": {"artifact_root": str(storage), "min_free_bytes": 10 * 1024**3, "durability": "local_durable",
                    "verification_ref": "local-preflight-" + output.name},
        "access": {"mode": "loopback", "bind_host": "127.0.0.1", "tls": False, "auth_secret_env": "AMPHORA_LOCAL_PREFLIGHT_TOKEN"},
        "provider": {"mode": "disabled", "endpoint": None, "model": None, "credential_env": None, "budget_usd_micros": 0, "data_policy": "deny"},
        "artifacts": artifacts}
    path = output / "profile.json"
    path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    env = {k:v for k,v in os.environ.items() if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC"}}
    env.update(PYTHONUTF8="1", AMPHORA_LOCAL_PREFLIGHT_TOKEN=secrets.token_urlsafe(32))
    def invoke(candidate, expected, environment):
        result = subprocess.run([str(python), "-I", "-m", "amphora_deployment", "preflight", "--profile", str(candidate)],
                                env=environment, capture_output=True, timeout=30)
        assert result.returncode == expected, result.stderr.decode()[-500:]
        return json.loads(result.stdout)
    accepted = invoke(path, 0, env)
    assert accepted["status"] == "preflight_passed"
    absent = invoke(path, 3, {k:v for k,v in env.items() if k != "AMPHORA_LOCAL_PREFLIGHT_TOKEN"})
    assert "missing_environment:AMPHORA_LOCAL_PREFLIGHT_TOKEN" in absent["blockers"]
    foreign = json.loads(json.dumps(profile))
    foreign["artifacts"][0]["architecture"] = "aarch64"
    other = output / "wrong-architecture.json"
    other.write_text(json.dumps(foreign), encoding="utf-8")
    rejected = invoke(other, 3, env)
    assert "artifact_target_incompatible" in rejected["blockers"]
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
        "selected_target": "owner_selected_local_computer", "profile": str(path), "profile_sha256": digest(path),
        "source_installation": str(installation / "manifest.json"), "storage": storage_evidence, "loopback": network_evidence,
        "preflight": accepted, "missing_credential": absent, "wrong_architecture": rejected,
        "limits": ["Native Windows process profile; Linux container images are not substituted for Windows executables",
                   "Pinned Runtime wheel closure only; full demo composition belongs to BP-09.02",
                   "Disposable preflight credential is environment-only; persistent service credentials are not provisioned",
                   "Storage normal-operation check does not establish power-loss durability or backup/restore"], "paid_calls": 0}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("Selected local host preflight and rejection probes passed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("output", "storage", "installation"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    verify(args.output, args.storage, args.installation, args.python.absolute())
