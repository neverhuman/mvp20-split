"""Original Planning execution report evidence owned by Runtime."""

from pathlib import Path

from alembic import op

revision = 'runtime_0027'
down_revision = 'runtime_0026'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
