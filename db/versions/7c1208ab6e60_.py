"""

Revision ID: 7c1208ab6e60
Revises: ca3b2fe82801
Create Date: 2024-05-03 11:38:57.525758

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7c1208ab6e60'
down_revision = 'ca3b2fe82801'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('jb_form',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('bot_id', sa.String(), nullable=True),
    sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['bot_id'], ['jb_bot.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('grievance_category_test_data')
    op.drop_table('grievance_category')
    op.drop_table('jb_fsm_state')
    op.drop_table('grievance_category_v2')
    op.add_column('jb_bot', sa.Column('timeout', sa.Integer(), nullable=True))
    op.add_column('jb_bot', sa.Column('supported_languages', sa.ARRAY(sa.String()), nullable=True))
    op.drop_constraint('jb_bot_phone_number_key', 'jb_bot', type_='unique')
    op.drop_column('jb_bot', 'phone_number')
    op.drop_column('jb_bot', 'status')
    op.add_column('jb_channel', sa.Column('status', sa.String(), nullable=False))
    op.add_column('jb_message', sa.Column('message', postgresql.JSON(astext_type=sa.Text()), nullable=False))
    op.create_foreign_key(None, 'jb_message', 'jb_channel', ['channel_id'], ['id'])
    op.drop_column('jb_message', 'media_url')
    op.drop_column('jb_message', 'message_text')
    op.drop_column('jb_message', 'channel')
    op.add_column('jb_session', sa.Column('variables', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.drop_constraint('jb_session_pid_fkey', 'jb_session', type_='foreignkey')
    op.drop_column('jb_session', 'pid')
    op.add_column('jb_turn', sa.Column('channel_id', sa.String(), nullable=True))
    op.add_column('jb_turn', sa.Column('user_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'jb_turn', 'jb_users', ['user_id'], ['id'])
    op.create_foreign_key(None, 'jb_turn', 'jb_channel', ['channel_id'], ['id'])
    op.drop_column('jb_turn', 'channel')
    op.add_column('jb_users', sa.Column('identifier', sa.String(), nullable=True))
    op.drop_column('jb_users', 'phone_number')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('jb_users', sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('jb_users', 'identifier')
    op.add_column('jb_turn', sa.Column('channel', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'jb_turn', type_='foreignkey')
    op.drop_constraint(None, 'jb_turn', type_='foreignkey')
    op.drop_column('jb_turn', 'user_id')
    op.drop_column('jb_turn', 'channel_id')
    op.add_column('jb_session', sa.Column('pid', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_foreign_key('jb_session_pid_fkey', 'jb_session', 'jb_users', ['pid'], ['id'])
    op.drop_column('jb_session', 'variables')
    op.add_column('jb_message', sa.Column('channel', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('jb_message', sa.Column('message_text', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('jb_message', sa.Column('media_url', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'jb_message', type_='foreignkey')
    op.drop_column('jb_message', 'message')
    op.drop_column('jb_channel', 'status')
    op.add_column('jb_bot', sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('jb_bot', sa.Column('phone_number', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_unique_constraint('jb_bot_phone_number_key', 'jb_bot', ['phone_number'])
    op.drop_column('jb_bot', 'supported_languages')
    op.drop_column('jb_bot', 'timeout')
    op.create_table('grievance_category_v2',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('ministry', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('subcategory', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('embedding', sa.NullType(), autoincrement=False, nullable=True),
    sa.Column('fields', postgresql.ARRAY(postgresql.JSON(astext_type=sa.Text())), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='grievance_category_v2_pkey')
    )
    op.create_table('jb_fsm_state',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('pid', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('state', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('variables', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('message', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='jb_fsm_state_pkey')
    )
    op.create_table('grievance_category',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('ministry', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('subcategory', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('embedding', sa.NullType(), autoincrement=False, nullable=True),
    sa.Column('fields', postgresql.ARRAY(postgresql.JSON(astext_type=sa.Text())), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='grievance_category_pkey')
    )
    op.create_table('grievance_category_test_data',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('ministry', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('category', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('subcategory', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('fields', postgresql.ARRAY(postgresql.JSON(astext_type=sa.Text())), autoincrement=False, nullable=True),
    sa.Column('persona', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='grievance_category_test_data_pkey')
    )
    op.drop_table('jb_form')
    # ### end Alembic commands ###