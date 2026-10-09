"""Private transactional launch journal; never stores or queries peer tables."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .intent import LaunchError, LaunchIntent
from .state import LaunchState, utc_now


class LaunchJournal:
    def __init__(self, directory: Path):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / 'launches.sqlite3'
        with self._connection() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS launches (
                tenant TEXT NOT NULL, project TEXT NOT NULL, actor TEXT NOT NULL, request_id TEXT NOT NULL,
                request BLOB NOT NULL, receipt BLOB NOT NULL, revision INTEGER NOT NULL,
                active INTEGER UNIQUE CHECK(active IS NULL OR active=1),
                PRIMARY KEY(tenant, project, actor, request_id))''')

    @contextmanager
    def _connection(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        try:
            db.execute('PRAGMA synchronous=FULL')
            yield db
        finally:
            db.close()

    @staticmethod
    def _state(row):
        if row is None:
            return None
        return LaunchState.restore(LaunchIntent.parse(row[0]), row[1])

    def get(self, key: tuple[str, str, str, str]):
        with self._connection() as db:
            return self._state(db.execute('SELECT request, receipt FROM launches WHERE tenant=? AND project=? AND actor=? AND request_id=?', key).fetchone())

    def active(self):
        with self._connection() as db:
            return self._state(db.execute('SELECT request, receipt FROM launches WHERE active=1').fetchone())

    def submit(self, intent: LaunchIntent, authorize_profile, *, now=utc_now):
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                existing = self._state(db.execute('SELECT request, receipt FROM launches WHERE tenant=? AND project=? AND actor=? AND request_id=?', intent.key).fetchone())
                if existing:
                    if existing.intent.request.sha256 != intent.request.sha256:
                        raise LaunchError('launch_request_conflict')
                    db.execute('COMMIT')
                    return existing
                if db.execute('SELECT 1 FROM launches WHERE active=1').fetchone():
                    raise LaunchError('launch_slot_busy')
                # Local pinned policy only: never hold this transaction over peer I/O.
                authorize_profile(intent)
                state = LaunchState.initial(intent, now())
                db.execute('INSERT INTO launches VALUES (?,?,?,?,?,?,?,1)', (*intent.key,
                    intent.request.canonical_bytes, state.receipt().model_dump_json().encode(), state.revision))
                db.execute('COMMIT')
                return state
            except BaseException:
                db.execute('ROLLBACK')
                raise

    def change(self, key, expected_revision: int, transition):
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                state = self._state(db.execute('SELECT request, receipt FROM launches WHERE tenant=? AND project=? AND actor=? AND request_id=?', key).fetchone())
                if state is None or state.revision != expected_revision:
                    raise LaunchError('launch_revision_conflict')
                updated = transition(state)
                if updated.intent != state.intent or updated.revision not in {state.revision, state.revision + 1}:
                    raise LaunchError('launch_transition_invalid')
                db.execute('UPDATE launches SET receipt=?, revision=?, active=? WHERE tenant=? AND project=? AND actor=? AND request_id=?',
                    (updated.receipt().model_dump_json().encode(), updated.revision, None if updated.terminal else 1, *key))
                db.execute('COMMIT')
                return updated
            except BaseException:
                db.execute('ROLLBACK')
                raise
