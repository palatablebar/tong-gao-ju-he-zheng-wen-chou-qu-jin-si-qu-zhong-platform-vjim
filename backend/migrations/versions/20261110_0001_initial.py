"""initial schema for dedupwire (sources / raw_items / articles / clusters /
cluster_members / suspected_edges / dedup_runs / events / users / audit_logs)

The schema is generated from the SQLAlchemy metadata so the ORM stays the single
source of truth; the migration itself is idempotent at the DDL level.
"""
from alembic import op

import src.models  # noqa: F401
from src.config.database import Base

revision = "20261110_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
