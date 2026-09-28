"""Exclusive generated-key writes under a service-owned root."""

import hashlib
import os
import re
import stat
from pathlib import Path

from ..publication.model import UploadError
from .lease import exclusive


def reject_links(path):
    for part in (path, *path.parents):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise UploadError("unsafe_storage_path")


class LocalBytes:
    def __init__(self, root: Path):
        if not root.is_absolute() or not root.is_dir():
            raise ValueError("Existing absolute service-owned root required")
        reject_links(root)
        self.root = root

    def path(self, key):
        if not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{32}", key):
            raise UploadError("invalid_storage_key")
        reject_links(self.root)
        path = self.root / key
        if path.exists() or path.is_symlink():
            reject_links(path)
        return path

    def sidecar(self, key, suffix):
        path = self.path(key).with_name(key + suffix)
        if path.exists() or path.is_symlink():
            reject_links(path)
        return path

    def guard(self, key):
        return exclusive(self.sidecar(key, ".lock"))

    def retire(self, key):
        """Caller holds guard; durable marker precedes unlink and forbids delayed writers."""
        marker = self.sidecar(key, ".retired")
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        self.path(key).unlink(missing_ok=True)

    def writer(self, attempt):
        guard = self.guard(attempt.storage_key)
        guard.__enter__()
        try:
            if self.sidecar(attempt.storage_key, ".retired").exists():
                raise UploadError("storage_key_retired")
            path = self.path(attempt.storage_key)
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path, flags, 0o600)
            return ByteWriter(os.fdopen(descriptor, "wb"), attempt.content, guard)
        except BaseException:
            guard.__exit__(None, None, None)
            raise

    def verify(self, key, content):
        """Read one immutable file; bytes/hash/size refer to the same open handle."""
        descriptor = os.open(self.path(key), os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0))
        payload = bytearray()
        with os.fdopen(descriptor, "rb") as handle:
            while chunk := handle.read(65536):
                if len(payload) + len(chunk) > content.size_bytes:
                    raise UploadError("content_integrity_mismatch")
                payload.extend(chunk)
        if len(payload) != content.size_bytes or hashlib.sha256(payload).hexdigest() != content.sha256:
            raise UploadError("content_integrity_mismatch")
        return bytes(payload)


class ByteWriter:
    def __init__(self, handle, expected, guard=None):
        self.guard = guard
        self.handle = handle
        self.expected = expected
        self.count = 0
        self.digest = hashlib.sha256()

    def write(self, chunk):
        if not isinstance(chunk, bytes):
            raise UploadError("invalid_content_chunk")
        if self.count + len(chunk) > self.expected.size_bytes:
            raise UploadError("content_size_mismatch")
        for start in range(0, len(chunk), 65536):
            part = chunk[start:start + 65536]
            self.handle.write(part)
            self.digest.update(part)
            self.count += len(part)

    def seal(self):
        if self.count != self.expected.size_bytes or self.digest.hexdigest() != self.expected.sha256:
            raise UploadError("content_integrity_mismatch")
        self.handle.flush()
        os.fsync(self.handle.fileno())

    def close(self):
        try:
            self.handle.close()
        finally:
            if self.guard is not None:
                self.guard.__exit__(None, None, None)
                self.guard = None
