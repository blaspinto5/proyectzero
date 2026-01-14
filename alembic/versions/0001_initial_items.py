"""initial items table

Revision ID: 0001_initial_items
Revises: 
Create Date: 2026-01-14 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_items'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('url', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('titulo', sa.Text()),
        sa.Column('precio', sa.Text()),
        sa.Column('stock', sa.Text()),
        sa.Column('raw', sa.Text()),
    )


def downgrade():
    op.drop_table('items')
