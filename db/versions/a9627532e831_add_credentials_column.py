"""Add credentials column

Revision ID: a9627532e831
Revises: 8fc0a0f4f22d
Create Date: 2024-02-22 18:17:30.756699

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a9627532e831'
down_revision = '8fc0a0f4f22d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('jb_bot', sa.Column('code', sa.String(), nullable=True))
    op.add_column('jb_bot', sa.Column('requirements', sa.String(), nullable=True))
    op.add_column('jb_bot', sa.Column('credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.drop_column('jb_bot', 'fsm_code')
    op.drop_column('jb_bot', 'requirements_txt')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('jb_bot', sa.Column('requirements_txt', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('jb_bot', sa.Column('fsm_code', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('jb_bot', 'credentials')
    op.drop_column('jb_bot', 'requirements')
    op.drop_column('jb_bot', 'code')
    # ### end Alembic commands ###