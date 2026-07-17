"""Create the ticket replies table."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0003_create_ticket_replies"
down_revision: str | None = "0002_create_tickets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ticket_replies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ticket_replies_author_id",
        "ticket_replies",
        ["author_id"],
    )
    op.create_index(
        "ix_ticket_replies_ticket_created_at",
        "ticket_replies",
        ["ticket_id", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ticket_replies_ticket_created_at",
        table_name="ticket_replies",
    )
    op.drop_index("ix_ticket_replies_author_id", table_name="ticket_replies")
    op.drop_table("ticket_replies")
