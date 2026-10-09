"""Offer idle installed executors before Runtime's independent eligibility check."""
from datetime import datetime, timedelta, timezone

from .ports import PeerUnavailable


class AdmissionCapacity:
    def __init__(self, supervisor, *, now=None):
        self.supervisor = supervisor
        self.now = now or (lambda: datetime.now(timezone.utc))

    def require_idle(self):
        rows = self.supervisor.scientific.status()
        if not rows or any(row['state'] not in {'quiescent', 'standby'}
                or row['faulted'] or row.get('active_turn', False) for row in rows.values()):
            raise PeerUnavailable()

    def offer(self):
        with self.supervisor.lock:
            self.require_idle()
            for name, row in self.supervisor.scientific.status().items():
                if row['state'] == 'quiescent':
                    self.supervisor.scientific_command(name, 'standby')
            # Standby creates no container/turn. Reporters perform fresh image,
            # dependency and Registry I/O on their existing background threads.
            self.supervisor.catalog.resume()
            reports = self.supervisor.catalog.status()
            names = set(self.supervisor.scientific.slots)
        now = self.now()
        if set(reports) != names:
            raise PeerUnavailable()
        for row in reports.values():
            observed = row.get('observation')
            if row['state'] != 'observed' or row.get('stopping') or not row.get('running') or not observed or observed['free_slots'] != 1:
                raise PeerUnavailable()
            try:
                at, expires = (datetime.fromisoformat(observed[key]) for key in ('observed_at', 'expires_at'))
                fresh = at <= now and now - at <= timedelta(seconds=5) and expires - now > timedelta(seconds=5)
            except (TypeError, ValueError, KeyError):
                fresh = False
            if not fresh:
                raise PeerUnavailable()
