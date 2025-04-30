"""add prediction fields

Revision ID: add_prediction_fields
Revises: create_predictions_table
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_prediction_fields'
down_revision = 'create_predictions_table'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to predictions table
    op.add_column('predictions', sa.Column('confidence', sa.Float(), nullable=True))
    op.add_column('predictions', sa.Column('model_version', sa.String(50), nullable=True))
    op.add_column('predictions', sa.Column('expected_goals_home', sa.Float(), nullable=True))
    op.add_column('predictions', sa.Column('expected_goals_away', sa.Float(), nullable=True))
    op.add_column('predictions', sa.Column('key_factors', sa.JSON(), nullable=True))

    # Update existing rows with default values
    op.execute("""
        UPDATE predictions 
        SET confidence = 0.85,
            model_version = '1.0.0',
            expected_goals_home = 1.8,
            expected_goals_away = 1.2,
            key_factors = '["Home team recent form", "Head to head record"]'
    """)

    # Make columns non-nullable after setting defaults
    op.alter_column('predictions', 'confidence', nullable=False)
    op.alter_column('predictions', 'model_version', nullable=False)
    op.alter_column('predictions', 'expected_goals_home', nullable=False)
    op.alter_column('predictions', 'expected_goals_away', nullable=False)
    op.alter_column('predictions', 'key_factors', nullable=False)


def downgrade():
    # Remove the new columns
    op.drop_column('predictions', 'key_factors')
    op.drop_column('predictions', 'expected_goals_away')
    op.drop_column('predictions', 'expected_goals_home')
    op.drop_column('predictions', 'model_version')
    op.drop_column('predictions', 'confidence') 