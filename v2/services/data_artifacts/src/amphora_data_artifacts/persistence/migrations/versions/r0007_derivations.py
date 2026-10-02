"""Immutable derived-upload declarations and atomic finalized lineage."""

from pathlib import Path

from alembic import op

revision = "artifact_0007"
down_revision = "artifact_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Derived publication requires an explicit forward migration")
