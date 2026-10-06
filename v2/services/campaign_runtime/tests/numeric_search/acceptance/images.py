"""Actual image-to-wheel identity and public Registry proofs for this fixture."""

import json
from pathlib import Path


class ImageCatalog:
    def __init__(self, config):
        self.entries, self.registrations = {}, []
        if config.get("images"):
            manifest = json.loads(Path(config["images"]).read_bytes())
            assert manifest["profile"] == "numeric-search-images-v1" and manifest.get("golden")
            for image in manifest["tools"]:
                for stage in image["descriptors"]:
                    assert stage not in self.entries
                    self.entries[stage] = image
            assert set(self.entries) == {"seed", "requests", "collect", "vary", "evaluate"}

    def digest(self, stage):
        return self.entries[stage]["image_manifest_digest"].removeprefix("sha256:") if self.entries else "c" * 64

    def verify(self, stage, descriptor, packages):
        if not self.entries:
            return
        image = self.entries[stage]
        assert descriptor == image["descriptors"][stage]
        owner = "evaluator" if stage == "evaluate" else "numeric"
        assert packages[owner]["wheels"] == image["local_wheels"], "Installed local wheel closure differs from image"

    def register(self, environment):
        if not self.entries:
            return
        e = environment
        e.registry = e.host("registry", "amphora_capability_registry", {
            "database_url_env": "DATABASE_URL", "principals": [e.principal("admin", ["register", "activate", "read"])],
            "resources": {"architecture": "x86_64", "operating_system": "linux", "cpu_millicores": 4000,
                "memory_mib": 4096, "gpu_count": 0, "timeout_seconds": 300,
                "max_parallel_invocations": 8, "max_batch_size": 128}}, "AMPHORA_REGISTRY_DATABASE_URL")
        for stage, release in e.releases.items():
            lock = e.release_locks[stage]
            registered = e.registry_call("register", {"scope": e.scope, "descriptor": release, "expected_lock": lock})
            assert registered["reason_code"] == "registered" and registered["release"]["lock"] == lock
            activated = e.registry_call("activate", {"release": lock, "expected_revision": 1})
            assert activated["status"] == "accepted" and activated["release"]["status"] == "active", activated
            self.registrations.append({"stage": stage, "registered": registered, "activated": activated})
