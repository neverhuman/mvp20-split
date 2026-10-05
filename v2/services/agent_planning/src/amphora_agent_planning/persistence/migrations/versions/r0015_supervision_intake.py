"""Original supervisor wrappers and atomic recording receipts."""

from pathlib import Path

from alembic import op

revision = 'planning_0015'
down_revision = 'planning_0014'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Retained Planning history requires an explicit forward migration')
