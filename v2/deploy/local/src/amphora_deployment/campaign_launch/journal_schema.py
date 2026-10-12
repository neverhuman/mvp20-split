"""Transactional local schema upgrade preserving original request/receipt bytes."""
from .intent import LaunchError, LaunchIntent
from .state import LaunchState

LEGACY = ('tenant', 'project', 'actor', 'request_id', 'request', 'receipt', 'revision', 'active')
CURRENT = (*LEGACY, 'family')
CREATE = '''CREATE TABLE launches (
    tenant TEXT NOT NULL, project TEXT NOT NULL, actor TEXT NOT NULL, request_id TEXT NOT NULL,
    request BLOB NOT NULL, receipt BLOB NOT NULL, revision INTEGER NOT NULL,
    active INTEGER UNIQUE CHECK(active IS NULL OR active=1),
    family TEXT NOT NULL CHECK(family IN ('campaign.launch','campaign.launch_successor')),
    PRIMARY KEY(tenant, project, actor, request_id, family))'''


def initialize(db):
    db.execute('BEGIN IMMEDIATE')
    try:
        columns = tuple(row[1] for row in db.execute('PRAGMA table_info(launches)'))
        if not columns:
            db.execute(CREATE)
        elif columns == LEGACY:
            # Validate old canonical data and index metadata before changing schema.
            for row in db.execute('SELECT * FROM launches'):
                state = LaunchState.restore(LaunchIntent.parse(row[4]), row[5])
                if state.intent.key != tuple(row[:4]) or state.revision != row[6] or row[7] != (None if state.terminal else 1):
                    raise LaunchError('launch_journal_corrupt')
            db.execute('ALTER TABLE launches RENAME TO launches_legacy_migration')
            db.execute(CREATE)
            db.execute("INSERT INTO launches SELECT *, 'campaign.launch' FROM launches_legacy_migration")
            db.execute('DROP TABLE launches_legacy_migration')
        elif columns != CURRENT:
            raise LaunchError('launch_journal_corrupt')
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise


def database_key(key):
    if len(key) == 4:
        return (*key, 'campaign.launch')
    if len(key) == 5 and key[-1] == 'campaign.launch_successor':
        return tuple(key)
    raise LaunchError('launch_request_invalid')
