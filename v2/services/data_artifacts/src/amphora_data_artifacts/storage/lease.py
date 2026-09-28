"""Persistent generated-key locks; all writers/cleaners participate."""

import os
from contextlib import contextmanager

if os.name == "nt":
    import msvcrt
else:
    import fcntl


@contextmanager
def exclusive(path):
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "r+b", buffering=0) as handle:
        if os.fstat(handle.fileno()).st_size == 0:
            handle.write(b"0")
        handle.seek(0)
        if os.name == "nt":
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
