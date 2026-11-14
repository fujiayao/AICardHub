"""company_affiliation_and_campaign

Revision ID: a7c3e91d5b20
Revises: cfe4fa4acaaa
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7c3e91d5b20"
down_revision: str | None = "cfe4fa4acaaa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "campaign",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("booth", sa.String(length=80), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("opening_override", sa.Text(), nullable=False),
        sa.Column("guide_override", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Employee affiliation: backfill historical rows to the primary company (min id).
    op.add_column("employee", sa.Column("company_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE employee SET company_id = (SELECT m.id FROM (SELECT MIN(id) AS id FROM company) m)"
    )
    bind = op.get_bind()
    missing = bind.execute(sa.text("SELECT COUNT(*) FROM employee WHERE company_id IS NULL"))
    if (missing.scalar() or 0) > 0:
        raise RuntimeError("employee rows exist without any company row; create company first")
    op.alter_column("employee", "company_id", existing_type=sa.Integer(), nullable=False)
    op.create_index(op.f("ix_employee_company_id"), "employee", ["company_id"], unique=False)
    op.create_foreign_key(
        "fk_employee_company_id", "employee", "company", ["company_id"], ["id"]
    )
    op.alter_column("employee", "phone", existing_type=sa.String(length=20), nullable=True)
    op.alter_column(
        "employee", "password_hash", existing_type=sa.String(length=100), nullable=True
    )

    # Attribution columns.
    op.add_column("visit", sa.Column("campaign_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_visit_campaign_id"), "visit", ["campaign_id"], unique=False)
    op.create_foreign_key("fk_visit_campaign_id", "visit", "campaign", ["campaign_id"], ["id"])

    op.add_column("chat_session", sa.Column("visit_id", sa.Integer(), nullable=True))
    op.add_column("chat_session", sa.Column("campaign_id", sa.Integer(), nullable=True))
    op.add_column(
        "chat_session",
        sa.Column("source", sa.String(length=20), nullable=False, server_default="link"),
    )
    op.create_index(
        op.f("ix_chat_session_campaign_id"), "chat_session", ["campaign_id"], unique=False
    )
    op.create_foreign_key(
        "fk_chat_session_visit_id",
        "chat_session",
        "visit",
        ["visit_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_chat_session_campaign_id", "chat_session", "campaign", ["campaign_id"], ["id"]
    )

    # Lead keeps its historical source values untouched.
    op.add_column("lead", sa.Column("visit_id", sa.Integer(), nullable=True))
    op.add_column("lead", sa.Column("campaign_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_lead_campaign_id"), "lead", ["campaign_id"], unique=False)
    op.create_foreign_key(
        "fk_lead_visit_id", "lead", "visit", ["visit_id"], ["id"], ondelete="SET NULL"
    )
    op.create_foreign_key("fk_lead_campaign_id", "lead", "campaign", ["campaign_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_lead_campaign_id", "lead", type_="foreignkey")
    op.drop_constraint("fk_lead_visit_id", "lead", type_="foreignkey")
    op.drop_index(op.f("ix_lead_campaign_id"), table_name="lead")
    op.drop_column("lead", "campaign_id")
    op.drop_column("lead", "visit_id")
    op.drop_constraint("fk_chat_session_campaign_id", "chat_session", type_="foreignkey")
    op.drop_constraint("fk_chat_session_visit_id", "chat_session", type_="foreignkey")
    op.drop_index(op.f("ix_chat_session_campaign_id"), table_name="chat_session")
    op.drop_column("chat_session", "source")
    op.drop_column("chat_session", "campaign_id")
    op.drop_column("chat_session", "visit_id")
    op.drop_constraint("fk_visit_campaign_id", "visit", type_="foreignkey")
    op.drop_index(op.f("ix_visit_campaign_id"), table_name="visit")
    op.drop_column("visit", "campaign_id")
    # Downgrade only succeeds when every employee still has credentials.
    op.alter_column(
        "employee", "password_hash", existing_type=sa.String(length=100), nullable=False
    )
    op.alter_column("employee", "phone", existing_type=sa.String(length=20), nullable=False)
    op.drop_constraint("fk_employee_company_id", "employee", type_="foreignkey")
    op.drop_index(op.f("ix_employee_company_id"), table_name="employee")
    op.drop_column("employee", "company_id")
    op.drop_table("campaign")
