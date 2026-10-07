"""Create-once encrypted credential file and explicit per-process environment selection."""

import json
import os
from pathlib import Path

from ..profile import ProfileError, label, require, secret_reference
from .protection import transform


class SecretBundle:
    def __init__(self, values):
        require(type(values) is dict and 1 <= len(values) <= 256, "credential_entries")
        for name, value in values.items():
            secret_reference(name, "credential_reference")
            require(type(value) is str and 1 <= len(value) <= 4096 and "\x00" not in value, "credential_value")
        self._values = dict(values)

    def __repr__(self):
        return "SecretBundle(" + str(len(self._values)) + " references)"

    @property
    def names(self):
        return tuple(sorted(self._values))

    def environment(self, names):
        names = tuple(names)
        require(all(name in self._values for name in names), "credential_reference_missing")
        return {name: self._values[name] for name in names}


class CredentialVault:
    def __init__(self, path, deployment_id):
        self.path = Path(path)
        self.deployment_id = label(deployment_id, "credential_deployment_id")
        self.context = ("amphora-local-credentials-v1:" + deployment_id).encode()

    def create(self, bundle):
        require(isinstance(bundle, SecretBundle), "credential_bundle")
        raw = json.dumps({"profile": "amphora-local-credentials-v1", "deployment_id": self.deployment_id,
                          "values": bundle.environment(bundle.names)}, sort_keys=True, separators=(",", ":")).encode()
        protected = transform(raw, self.context, protect=True)
        # Exclusive creation deliberately forbids accidental rotation/replacement.
        # A partial write fails closed on load; no implicit regeneration is permitted.
        with self.path.open("xb") as stream:
            stream.write(protected)
            stream.flush()
            os.fsync(stream.fileno())

    def load(self):
        with self.path.open("rb") as stream:
            protected = stream.read(131073)
        raw = transform(protected, self.context, protect=False)
        try:
            record = json.loads(raw)
        except (ValueError, RecursionError):
            raise ProfileError("credential_payload_invalid") from None
        require(type(record) is dict and set(record) == {"profile", "deployment_id", "values"}, "credential_payload_shape")
        require(record["profile"] == "amphora-local-credentials-v1" and record["deployment_id"] == self.deployment_id,
                "credential_payload_binding")
        return SecretBundle(record["values"])
