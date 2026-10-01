"""Explicit rights revisions/current heads; historical sources acquire no implicit grants."""

from pathlib import Path

from alembic import op

revision = "artifact_0006"
down_revision = "artifact_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Source rights require an explicit forward migration")
