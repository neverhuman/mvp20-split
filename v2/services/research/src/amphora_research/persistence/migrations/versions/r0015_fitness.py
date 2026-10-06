"""Immutable synthetic fitness projections; source history cannot be rewritten."""
from pathlib import Path
from alembic import op

revision = "research_0015"
down_revision = "research_0014"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix('.sql').read_text(encoding='utf-8'))


def downgrade():
    raise RuntimeError("Fitness history requires a forward migration")
