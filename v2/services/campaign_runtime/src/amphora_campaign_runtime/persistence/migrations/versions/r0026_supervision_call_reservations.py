"""Conservative potential-call reservations tied to original outgoing requests."""

from pathlib import Path

from alembic import op

revision = 'runtime_0026'
down_revision = 'runtime_0025'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
