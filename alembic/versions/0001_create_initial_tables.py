"""create initial tables

Revision ID: 0001
Revises: 
Create Date: 2025-08-22 00:00:00.000000
"""
from alembic import op  # type: ignore
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('symbol', sa.Text, nullable=False),
        sa.Column('side', sa.Text, nullable=False),
        sa.Column('qty', sa.Float, nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('status', sa.Text, nullable=False),
        sa.Column('ts', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )
    op.create_table(
        'fills',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('qty', sa.Float, nullable=False),
        sa.Column('ts', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )
    op.create_table(
        'positions',
        sa.Column('symbol', sa.Text, primary_key=True),
        sa.Column('qty', sa.Float, nullable=False),
        sa.Column('avg_price', sa.Float, nullable=False),
    )


def downgrade():
    op.drop_table('positions')
    op.drop_table('fills')
    op.drop_table('orders')
