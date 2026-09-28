"""Initial artifact record constraints; command behavior is a later child."""

from pathlib import Path

from alembic import op

revision = "artifact_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Evidence-bearing artifact schema requires an explicit forward migration")
