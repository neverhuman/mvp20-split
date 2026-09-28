"""Conservative cleanup states; existing uploads begin a fresh grace interval."""

from pathlib import Path

from alembic import op

revision = "artifact_0003"
down_revision = "artifact_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Upload evidence requires a forward migration")
