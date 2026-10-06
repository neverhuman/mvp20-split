"""Immutable checkpoint completion; separate from attempts and usage."""

from pathlib import Path

from alembic import op

revision = 'planning_0018'
down_revision = 'planning_0017'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
