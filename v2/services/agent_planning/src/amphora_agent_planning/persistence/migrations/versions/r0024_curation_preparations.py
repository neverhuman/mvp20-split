"""Original prepared curation input linkage; no provider issuance."""
from pathlib import Path
from alembic import op

revision = 'planning_0024'
down_revision = 'planning_0023'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError('Evidence-bearing schema requires an explicit forward migration')
