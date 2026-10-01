"""Immutable lookup intents and first committed Research identity observations."""

from pathlib import Path

from alembic import op

revision = "artifact_0005"
down_revision = "artifact_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Identity observations require an explicit forward migration")
