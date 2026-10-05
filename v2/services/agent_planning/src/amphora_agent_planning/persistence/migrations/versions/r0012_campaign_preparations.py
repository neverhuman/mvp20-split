"""Immutable campaign packet and input-selection evidence."""

from pathlib import Path

from alembic import op

revision = 'planning_0012'
down_revision = 'planning_0011'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Campaign preparation history requires a forward migration')
