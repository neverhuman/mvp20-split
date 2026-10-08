"""Single-use launcher tickets and restart-invalidated browser sessions."""

import hashlib
import secrets
import threading
import time


class SessionDenied(ValueError):
    pass


def fingerprint(token):
    if type(token) is not str or not 32 <= len(token) <= 128 or not token.isascii():
        raise SessionDenied("session_denied")
    return hashlib.sha256(token.encode()).hexdigest()


class Sessions:
    def __init__(self, *, clock=time.monotonic, ticket_lifetime=60):
        if type(ticket_lifetime) is not int or not 1<=ticket_lifetime<=300:
            raise ValueError('ticket_lifetime')
        self.ticket_lifetime=ticket_lifetime
        self.clock = clock
        self.tickets, self.sessions = {}, {}
        self.lock = threading.Lock()

    def _expire(self):
        now = self.clock()
        self.tickets = {key:expiry for key,expiry in self.tickets.items() if expiry > now}
        self.sessions = {key:expiry for key,expiry in self.sessions.items() if expiry > now}

    def issue_ticket(self):
        with self.lock:
            self._expire()
            if len(self.tickets) >= 16:
                raise SessionDenied("ticket_capacity")
            token = secrets.token_urlsafe(36)
            self.tickets[fingerprint(token)] = self.clock() + self.ticket_lifetime
            return token

    def exchange(self, ticket):
        key = fingerprint(ticket)
        with self.lock:
            self._expire()
            if key not in self.tickets or len(self.sessions) >= 8:
                raise SessionDenied("session_denied")
            self.tickets.pop(key)
            token = secrets.token_urlsafe(36)
            self.sessions[fingerprint(token)] = self.clock() + 8 * 3600
            return token

    def authenticate(self, token):
        key = fingerprint(token)
        with self.lock:
            self._expire()
            if key not in self.sessions:
                raise SessionDenied("session_denied")

    def revoke(self, token):
        key = fingerprint(token)
        with self.lock:
            self.sessions.pop(key, None)
