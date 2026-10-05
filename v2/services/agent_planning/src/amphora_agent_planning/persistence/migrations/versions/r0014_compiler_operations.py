"""Immutable compiler commands, bounded check rounds and event histories."""

from pathlib import Path

from alembic import op

revision = 'planning_0014'
down_revision = 'planning_0013'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Compiler operation history requires a forward migration')
