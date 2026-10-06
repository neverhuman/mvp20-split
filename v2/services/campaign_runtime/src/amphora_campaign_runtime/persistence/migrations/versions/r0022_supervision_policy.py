"""Append-only exact policy pins; existing runs remain unsupervised."""

from pathlib import Path

from alembic import op

revision = 'runtime_0022'
down_revision = 'runtime_0021'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
