"""add French translation columns to themes, difficulties, tones

Revision ID: b1f2c3d4e5a6
Revises: ea25d4c5f272
Create Date: 2026-06-30

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b1f2c3d4e5a6"
down_revision = "ea25d4c5f272"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("themes", sa.Column("label_fr", sa.Text(), nullable=True))
    op.add_column("themes", sa.Column("era_fr", sa.Text(), nullable=True))
    op.add_column("themes", sa.Column("setting_fr", sa.Text(), nullable=True))

    op.add_column("difficulties", sa.Column("label_fr", sa.Text(), nullable=True))
    op.add_column("difficulties", sa.Column("description_fr", sa.Text(), nullable=True))

    op.add_column("tones", sa.Column("label_fr", sa.Text(), nullable=True))
    op.add_column("tones", sa.Column("description_fr", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("tones", "description_fr")
    op.drop_column("tones", "label_fr")

    op.drop_column("difficulties", "description_fr")
    op.drop_column("difficulties", "label_fr")

    op.drop_column("themes", "setting_fr")
    op.drop_column("themes", "era_fr")
    op.drop_column("themes", "label_fr")
