"""Attributable immutable request repair or fallback disposition."""

from pathlib import Path

from alembic import op

revision = 'runtime_0028'
down_revision = 'runtime_0027'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
