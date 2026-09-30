"""Reject SQL NULL predecessor bypass for revisions beyond one."""

from pathlib import Path

from alembic import op

revision = "research_0002"
down_revision = "research_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Research predecessor constraints require an explicit forward migration")
