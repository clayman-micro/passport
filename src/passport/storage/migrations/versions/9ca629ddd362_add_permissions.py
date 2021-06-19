"""Add permissions

Revision ID: 9ca629ddd362
Revises: 615677fb3a4f
Create Date: 2020-09-09 23:37:57.555057

"""
import sqlalchemy as sa  # type: ignore
from alembic import op  # type: ignore

# revision identifiers, used by Alembic.
revision = "9ca629ddd362"
down_revision = "615677fb3a4f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "permission_id"),
    )
    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("users", "is_superuser")
    op.drop_table("user_permissions")
    op.drop_table("permissions")
