"""Bounded Docker adapter; never records raw inspect data or credential-bearing stderr."""

import json
import os
import subprocess

from ..profile import ProfileError


class Docker:
    def run(self, *arguments, payload=None, secrets=None, allow_failure=False):
        environment = {k:v for k,v in os.environ.items() if k.upper() in {
            "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}}
        environment.update(secrets or {})
        try:
            result = subprocess.run(["docker", *arguments], input=payload, env=environment,
                                    capture_output=True, text=True, encoding="utf-8", timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            raise ProfileError("deployment_docker_unavailable") from None
        if result.returncode != 0:
            if allow_failure:
                return None
            raise ProfileError("deployment_docker_operation_failed")
        return result.stdout.strip()

    def inspect(self, kind, name):
        raw = self.run(kind, "inspect", name, allow_failure=True)
        return None if raw is None else json.loads(raw)[0]
