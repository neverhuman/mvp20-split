import pytest


@pytest.fixture
def record():
    return {"schema_version": "1", "profile_id": "synthetic-preflight", "target": {
        "host_id": "not-a-selected-host", "operating_system": "linux", "architecture": "x86_64", "python": "3.12",
        "min_cpu_count": 2, "min_memory_bytes": 1024, "accelerator": "none"},
        "storage": {"artifact_root": "/var/lib/amphora", "min_free_bytes": 4096, "durability": "unverified", "verification_ref": None},
        "access": {"mode": "loopback", "bind_host": "127.0.0.1", "tls": False, "auth_secret_env": "DEMO_AUTH"},
        "provider": {"mode": "disabled", "endpoint": None, "model": None, "credential_env": None,
                     "budget_usd_micros": 0, "data_policy": "deny"},
        "artifacts": [{"name": "example", "release": "0.1.0", "sha256": "a" * 64,
                       "operating_system": "linux", "architecture": "x86_64"}]}

