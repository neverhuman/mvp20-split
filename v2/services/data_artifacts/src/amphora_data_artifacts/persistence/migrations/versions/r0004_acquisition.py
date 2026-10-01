"""Immutable acquisition delivery/revision and conversion trace history."""

from pathlib import Path

from alembic import op

revision = "artifact_0004"
down_revision = "artifact_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Acquisition evidence requires an explicit forward migration")
