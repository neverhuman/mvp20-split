"""Private immutable encoding identities/results with narrowly mutable compute leases."""

from pathlib import Path

from alembic import op

revision = "artifact_0008"
down_revision = "artifact_0007"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade():
    raise RuntimeError("Representation history requires an explicit forward migration")
