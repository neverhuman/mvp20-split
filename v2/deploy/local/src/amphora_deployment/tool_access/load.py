"""Bounded listener admission and payload-free connection pressure evidence."""

import threading


class ConnectionLoad:
    def __init__(self, limit):
        self.limit = limit
        self._lock = threading.Lock()
        self._active = self._peak = self._admitted = self._denied = 0

    def acquire(self):
        with self._lock:
            if self._active == self.limit:
                self._denied += 1
                return False
            self._active += 1
            self._admitted += 1
            self._peak = max(self._peak, self._active)
            return True

    def release(self):
        with self._lock:
            if self._active < 1:
                raise RuntimeError('tool_tls_connection_release')
            self._active -= 1

    def snapshot(self):
        with self._lock:
            return {'limit': self.limit, 'active': self._active, 'peak': self._peak,
                    'admitted': self._admitted, 'denied': self._denied}
