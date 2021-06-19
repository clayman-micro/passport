"""Add sessions

Revision ID: a01d1258d7a7
Revises: 9ca629ddd362
Create Date: 2020-09-10 13:16:28.154448

"""
import sqlalchemy as sa  # type: ignore
from alembic import op  # type: ignore

# revision identifiers, used by Alembic.
revision = "a01d1258d7a7"
down_revision = "9ca629ddd362"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sessions",
        sa.Column("key", sa.String(length=44), nullable=False),
        sa.Column("expires", sa.DateTime(), nullable=True),
        sa.Column("user", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade():
    op.drop_table("sessions")
