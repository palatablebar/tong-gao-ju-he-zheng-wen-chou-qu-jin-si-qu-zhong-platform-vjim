"""reextract: per-source body re-extraction batches (additive, safe on existing data)

Existing installs already ran 20261110_0001; this migration only adds the two new
tables. Re-running it is a no-op thanks to ``checkfirst``.
"""
from alembic import op

import src.models  # noqa: F401
from src.config.database import Base
from src.models.reextract import ReextractBatch, ReextractItem

revision = "20261112_0002"
down_revision = "20261110_0001"
branch_labels = None
depends_on = None

TABLE_NAMES = [ReextractBatch.__tablename__, ReextractItem.__tablename__]


def upgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[name] for name in TABLE_NAMES]
    Base.metadata.create_all(bind=bind, tables=tables, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for table in reversed([Base.metadata.tables[name] for name in TABLE_NAMES]):
        table.drop(bind=bind, checkfirst=True)
