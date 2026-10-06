"""Frozen evaluation protocols/inputs; physical attempts retain their existing journals."""

from pathlib import Path

from alembic import op

revision = 'planning_0019'
down_revision = 'planning_0018'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
