"""added jbchannel

Revision ID: 269472c9d076
Revises: 159ddccc1ed1
Create Date: 2024-04-17 16:56:30.205256

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '269472c9d076'
down_revision = '159ddccc1ed1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('jb_channel',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('bot_id', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('key', sa.String(), nullable=True),
    sa.Column('app_id', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['bot_id'], ['jb_bot.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.alter_column('jb_bot', 'channels',
    #            existing_type=postgresql.JSON(astext_type=sa.Text()),
    #            type_=sa.ARRAY(sa.String()),
    #            existing_nullable=True)
    op.add_column('jb_session', sa.Column('channel_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'jb_session', 'jb_channel', ['channel_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'jb_session', type_='foreignkey')
    op.drop_column('jb_session', 'channel_id')
    # op.alter_column('jb_bot', 'channels',
    #            existing_type=sa.ARRAY(sa.String()),
    #            type_=postgresql.JSON(astext_type=sa.Text()),
    #            existing_nullable=True)
    op.drop_table('jb_channel')
    # ### end Alembic commands ###