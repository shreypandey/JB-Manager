"""Added refactored data model

Revision ID: a393f2398866
Revises: fd76a381bc20
Create Date: 2024-07-15 11:12:27.510421

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a393f2398866"
down_revision = "fd76a381bc20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "jb_message",
        sa.Column("message", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.drop_column("jb_message", "channel")
    op.drop_column("jb_message", "message_text")
    op.drop_column("jb_message", "media_url")
    op.drop_column("jb_message", "channel_id")
    op.add_column("jb_session", sa.Column("user_id", sa.String(), nullable=True))
    op.drop_constraint("jb_session_pid_fkey", "jb_session", type_="foreignkey")
    op.create_foreign_key(None, "jb_session", "jb_users", ["user_id"], ["id"])
    op.drop_column("jb_session", "pid")
    op.add_column("jb_turn", sa.Column("bot_id", sa.String(), nullable=True))
    op.add_column("jb_turn", sa.Column("user_id", sa.String(), nullable=True))
    op.add_column(
        "jb_turn",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_foreign_key(None, "jb_turn", "jb_users", ["user_id"], ["id"])
    op.create_foreign_key(None, "jb_turn", "jb_bot", ["bot_id"], ["id"])
    op.drop_column("jb_turn", "channel")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "jb_turn",
        sa.Column("channel", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(None, "jb_turn", type_="foreignkey")
    op.drop_constraint(None, "jb_turn", type_="foreignkey")
    op.drop_column("jb_turn", "created_at")
    op.drop_column("jb_turn", "user_id")
    op.drop_column("jb_turn", "bot_id")
    op.add_column(
        "jb_session", sa.Column("pid", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(None, "jb_session", type_="foreignkey")
    op.create_foreign_key(
        "jb_session_pid_fkey", "jb_session", "jb_users", ["pid"], ["id"]
    )
    op.drop_column("jb_session", "user_id")
    op.add_column(
        "jb_message",
        sa.Column("channel_id", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "jb_message",
        sa.Column("media_url", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "jb_message",
        sa.Column("message_text", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "jb_message",
        sa.Column("channel", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_column("jb_message", "message")
    # ### end Alembic commands ###
