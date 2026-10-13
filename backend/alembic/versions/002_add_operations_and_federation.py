"""add_operations_and_federation

Revision ID: 002_add_operations_and_federation
Revises: 00ffa2457dcf
Create Date: 2026-10-13 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_ops_and_federation'
down_revision: Union[str, None] = '00ffa2457dcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. operations_inventory_items
    op.create_table(
        'operations_inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=False),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('quantity_on_hand', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reorder_threshold', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('warehouse_location', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='in_stock'),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_operations_inventory_items_department_id'), 'operations_inventory_items', ['department_id'], unique=False)
    op.create_index(op.f('ix_operations_inventory_items_id'), 'operations_inventory_items', ['id'], unique=False)
    op.create_index(op.f('ix_operations_inventory_items_sku'), 'operations_inventory_items', ['sku'], unique=True)

    # 2. department_agents
    op.create_table(
        'department_agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('agent_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('system_prompt', sa.Text(), nullable=False, server_default=''),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('department_id')
    )
    op.create_index(op.f('ix_department_agents_agent_code'), 'department_agents', ['agent_code'], unique=True)
    op.create_index(op.f('ix_department_agents_department_id'), 'department_agents', ['department_id'], unique=True)
    op.create_index(op.f('ix_department_agents_id'), 'department_agents', ['id'], unique=False)

    # 3. federation_access_requests
    op.create_table(
        'federation_access_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('requester_user_id', sa.Integer(), nullable=False),
        sa.Column('requester_department_id', sa.Integer(), nullable=False),
        sa.Column('requesting_agent', sa.String(length=50), nullable=False),
        sa.Column('source_department_id', sa.Integer(), nullable=False),
        sa.Column('business_purpose', sa.String(length=255), nullable=False),
        sa.Column('requested_fields', sa.JSON(), nullable=False),
        sa.Column('record_identifiers', sa.JSON(), nullable=False),
        sa.Column('access_duration_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('approver_user_id', sa.Integer(), nullable=True),
        sa.Column('decision_reason', sa.Text(), nullable=True),
        sa.Column('approved_fields', sa.JSON(), nullable=True),
        sa.Column('approved_record_ids', sa.JSON(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approver_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['requester_department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['requester_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['source_department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_federation_access_requests_idempotency_key'), 'federation_access_requests', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_federation_access_requests_requester_department_id'), 'federation_access_requests', ['requester_department_id'], unique=False)
    op.create_index(op.f('ix_federation_access_requests_requester_user_id'), 'federation_access_requests', ['requester_user_id'], unique=False)
    op.create_index(op.f('ix_federation_access_requests_source_department_id'), 'federation_access_requests', ['source_department_id'], unique=False)
    op.create_index(op.f('ix_federation_access_requests_status'), 'federation_access_requests', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_federation_access_requests_status'), table_name='federation_access_requests')
    op.drop_index(op.f('ix_federation_access_requests_source_department_id'), table_name='federation_access_requests')
    op.drop_index(op.f('ix_federation_access_requests_requester_user_id'), table_name='federation_access_requests')
    op.drop_index(op.f('ix_federation_access_requests_requester_department_id'), table_name='federation_access_requests')
    op.drop_index(op.f('ix_federation_access_requests_idempotency_key'), table_name='federation_access_requests')
    op.drop_table('federation_access_requests')

    op.drop_index(op.f('ix_department_agents_id'), table_name='department_agents')
    op.drop_index(op.f('ix_department_agents_department_id'), table_name='department_agents')
    op.drop_index(op.f('ix_department_agents_agent_code'), table_name='department_agents')
    op.drop_table('department_agents')

    op.drop_index(op.f('ix_operations_inventory_items_sku'), table_name='operations_inventory_items')
    op.drop_index(op.f('ix_operations_inventory_items_id'), table_name='operations_inventory_items')
    op.drop_index(op.f('ix_operations_inventory_items_department_id'), table_name='operations_inventory_items')
    op.drop_table('operations_inventory_items')
