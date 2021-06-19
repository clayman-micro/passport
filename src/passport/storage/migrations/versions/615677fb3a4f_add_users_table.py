"""
Add users table

Revision ID: 615677fb3a4f
Revises:
Create Date: 2020-09-09 21:36:41.102344

"""

import sqlalchemy  # type: ignore
from alembic import op  # type: ignore


# revision identifiers, used by Alembic.
revision = "615677fb3a4f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sqlalchemy.Column("id", sqlalchemy.Integer(), nullable=False),
        sqlalchemy.Column("email", sqlalchemy.String(length=255), nullable=False),
        sqlalchemy.Column("password", sqlalchemy.String(length=255), nullable=False),
        sqlalchemy.Column("is_active", sqlalchemy.Boolean(), nullable=True),
        sqlalchemy.Column("last_login", sqlalchemy.DateTime(), nullable=True),
        sqlalchemy.Column("created_on", sqlalchemy.DateTime(), nullable=True),
        sqlalchemy.PrimaryKeyConstraint("id"),
        sqlalchemy.UniqueConstraint("email"),
    )


def downgrade():
    op.drop_table("users")
