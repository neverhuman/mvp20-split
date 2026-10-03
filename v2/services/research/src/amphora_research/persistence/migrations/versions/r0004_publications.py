"""Research-owned publication leases and immutable history."""

from pathlib import Path

from alembic import op

revision = "research_0004"
down_revision = "research_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Publication history requires an explicit forward migration")
