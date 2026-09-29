"""Immutable aggregate observations linked to their atomic closure audit."""

from pathlib import Path

from alembic import op

revision = "runtime_0008"
down_revision = "runtime_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Evidence-bearing runtime schema requires an explicit forward migration")
