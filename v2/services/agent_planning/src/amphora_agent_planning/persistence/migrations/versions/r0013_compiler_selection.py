"""Immutable compiler selections with separate fenced controls."""

from pathlib import Path

from alembic import op

revision = 'planning_0013'
down_revision = 'planning_0012'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Compiler selection history requires a forward migration')
