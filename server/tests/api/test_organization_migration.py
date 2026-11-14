"""Real MySQL regression: rejected downgrade must not execute partial DDL."""

import importlib.util
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import delete, select, text
from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.modules.workspace.models import Company, Employee

pytest_plugins = ["test_backend_isolation"]


@pytest.mark.parametrize("missing_field", ["phone", "password_hash"])
async def test_拒绝降级在任何DDL之前且保留完整结构(db, missing_field):
    url = make_url(get_settings().test_database_url)
    assert url.database == "aicardhub_test"
    assert url.host in {"localhost", "127.0.0.1", "::1"}
    company = Company(name="合成迁移拒绝测试" + uuid4().hex[:8])
    db.add(company)
    await db.flush()
    employee = Employee(
        name="合成迁移拒绝测试",
        company_id=company.id,
        phone=None if missing_field == "phone" else "138" + str(uuid4().int)[-8:],
        password_hash=None if missing_field == "password_hash" else "synthetic-not-a-login",
        role="employee",
    )
    db.add(employee)
    await db.commit()
    employee_id, company_id = employee.id, company.id
    path = (
        Path(__file__).parents[2]
        / "alembic/versions/a7c3e91d5b20_company_affiliation_and_campaign.py"
    )
    spec = importlib.util.spec_from_file_location("organization_migration_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    schema_query = text(
        "SELECT TABLE_NAME, COLUMN_NAME, IS_NULLABLE FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME IN "
        "('campaign','employee','visit','chat_session','lead') "
        "ORDER BY TABLE_NAME, ORDINAL_POSITION"
    )
    constraints_query = text(
        "SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, COLUMN_NAME "
        "FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = DATABASE() "
        "AND TABLE_NAME IN ('campaign','employee','visit','chat_session','lead') "
        "ORDER BY TABLE_NAME, CONSTRAINT_NAME, ORDINAL_POSITION"
    )
    try:
        before = (await db.execute(schema_query)).all()
        constraints_before = (await db.execute(constraints_query)).all()
        version_before = (await db.execute(text("SELECT version_num FROM alembic_version"))).all()
        assert any(row.TABLE_NAME == "campaign" for row in before)
        assert any(row.CONSTRAINT_NAME == "fk_lead_campaign_id" for row in constraints_before)
        connection = await db.connection()

        def downgrade(sync_connection):
            context = MigrationContext.configure(sync_connection)
            with Operations.context(context):
                module.downgrade()

        with pytest.raises(RuntimeError, match="NULL phone or password_hash"):
            await connection.run_sync(downgrade)
        assert (await db.execute(schema_query)).all() == before
        assert (await db.execute(constraints_query)).all() == constraints_before
        assert (
            await db.execute(text("SELECT version_num FROM alembic_version"))
        ).all() == version_before
        assert await db.scalar(select(Employee.id).where(Employee.id == employee_id)) == employee_id
    finally:
        await db.rollback()
        await db.execute(delete(Employee).where(Employee.id == employee_id))
        await db.execute(delete(Company).where(Company.id == company_id))
        await db.commit()
