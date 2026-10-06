"""Request-locked completion fence, with no dependency on report orchestration."""

from sqlalchemy import text

from ..context.policy import require


def require_execution_open(connection, key):
    closed = connection.execute(text('SELECT 1 FROM planning.checkpoint_execution_reports '
        'WHERE tenant_id=:tenant AND project_id=:project AND engagement_id=:engagement'), key).first()
    require(closed is None, 'checkpoint_execution_completed')
