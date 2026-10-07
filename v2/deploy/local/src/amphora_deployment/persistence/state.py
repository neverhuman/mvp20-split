"""Owned deployment identity and single-operator journal; no fixture discovery/reset."""

import json
import os
import uuid
from pathlib import Path

from ..profile import ProfileError, require


LABEL = "amphora.local-deployment"


class LocalState:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.path = self.root / "stores.json"
        self.record = None
        self._lock = None

    def __enter__(self):
        require(os.name == "nt", "deployment_platform_unsupported")
        import msvcrt
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = (self.root / ".operation.lock").open("a+b")
        self._lock.seek(0, os.SEEK_END)
        if self._lock.tell() == 0:
            self._lock.write(b"1")
            self._lock.flush()
        self._lock.seek(0)
        try:
            msvcrt.locking(self._lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            self._lock.close()
            self._lock = None
            raise ProfileError("deployment_operation_busy") from None
        try:
            if self.path.exists():
                self.record = json.loads(self.path.read_bytes())
                require(type(self.record) is dict and self.record.get("schema_version") == "1", "deployment_state_shape")
                identity = self.record.get("deployment_id")
                require(type(identity) is str and len(identity) == 32 and all(c in "0123456789abcdef" for c in identity), "deployment_state_identity")
            else:
                self.record = {"schema_version": "1", "deployment_id": uuid.uuid4().hex, "phase": "declared"}
                self.save()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *unused):
        if self._lock is not None:
            import msvcrt
            self._lock.seek(0)
            msvcrt.locking(self._lock.fileno(), msvcrt.LK_UNLCK, 1)
            self._lock.close()
            self._lock = None

    @property
    def identity(self):
        return self.record["deployment_id"]

    def name(self, suffix):
        require(suffix in ("postgres", "postgres-data", "qdrant", "qdrant-data"), "deployment_resource_kind")
        return "amphora-local-" + self.identity + "-" + suffix

    def save(self):
        temporary = self.path.with_name(".stores-" + uuid.uuid4().hex + ".tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(json.dumps(self.record, sort_keys=True, indent=2).encode())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)
