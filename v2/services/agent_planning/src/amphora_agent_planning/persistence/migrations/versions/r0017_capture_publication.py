"""Owned immutable capture uploads and response exchange history."""

from pathlib import Path

from alembic import op

revision = 'planning_0017'
down_revision = 'planning_0016'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
