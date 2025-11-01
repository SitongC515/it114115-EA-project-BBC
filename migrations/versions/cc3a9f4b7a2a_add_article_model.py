"""add article model

Revision ID: cc3a9f4b7a2a
Revises: b1dc227f99bc
Create Date: 2025-11-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'cc3a9f4b7a2a'
down_revision = 'b1dc227f99bc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'article',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('headline', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.String(length=512), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=True, index=False),
        sa.Column('image_url', sa.String(length=512), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
    )


def downgrade():
    op.drop_table('article')
