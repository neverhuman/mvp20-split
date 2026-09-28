"""Immutable releases, revisioned inventory and terminal command receipts."""

from pathlib import Path

from alembic import op

revision = "registry_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Evidence-bearing registry requires an explicit forward migration")
