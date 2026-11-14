"""Bounded administrator import workflows. Uploads return drafts, never approvals."""

from io import BytesIO
from pathlib import PurePath
from typing import Any
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

import frontmatter
from openpyxl import load_workbook
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from yaml import YAMLError

from app.core.errors import AppError, ErrorCode
from app.kb.loader import parse_document
from app.modules.workspace import repo
from app.modules.workspace import schemas as s
from app.modules.workspace import service as shared
from app.modules.workspace.models import Employee

MAX_UPLOAD = 20 * 1024 * 1024
MAX_ROWS = 500
HEADERS = {
    "姓名": "name",
    "手机号": "phone",
    "手机": "phone",
    "部门": "dept",
    "职位": "title",
    "初始密码": "password",
    "密码": "password",
    "邮箱": "email",
    "负责业务": "business_scope",
    "角色": "role",
}


def parse_employees(content: bytes, filename: str) -> list[tuple[int, dict[str, Any]]]:
    if not filename.lower().endswith(".xlsx") or len(content) > MAX_UPLOAD:
        raise AppError(ErrorCode.VALIDATION_ERROR, 422, "仅支持20MB以内的xlsx文件")
    try:
        with ZipFile(BytesIO(content)) as archive:
            if (
                len(archive.infolist()) > 2000
                or sum(item.file_size for item in archive.infolist()) > 50 * 1024 * 1024
            ):
                raise ValueError("expanded workbook too large")
        workbook = load_workbook(
            BytesIO(content), read_only=True, data_only=False, keep_links=False
        )
        try:
            sheet = workbook.active
            if sheet is None:
                raise ValueError("no worksheet")
            rows = sheet.iter_rows(max_row=MAX_ROWS + 2, max_col=15)
            first = next(rows)
            names = [
                HEADERS.get(str(cell.value).strip(), str(cell.value).strip())
                if cell.value is not None
                else ""
                for cell in first
            ]
            defined = [key for key in names if key]
            if (
                len(set(defined)) != len(defined)
                or not {"name", "phone", "password"}.issubset(defined)
                or any(key not in s.EmployeeInput.model_fields for key in defined)
            ):
                raise ValueError("invalid headers")
            result = []
            for number, cells in enumerate(rows, 2):
                if not any(cell.value is not None for cell in cells):
                    continue
                if number > MAX_ROWS + 1:
                    raise ValueError("too many rows")
                values: dict[str, Any] = {}
                for key, cell in zip(names, cells, strict=True):
                    if key and cell.value is not None:
                        if cell.data_type == "f":
                            values["_error"] = "不支持公式单元格"
                            break
                        value = cell.value
                        if (
                            key == "phone"
                            and isinstance(value, (int, float))
                            and float(value).is_integer()
                        ):
                            value = str(int(value))
                        values[key] = str(value).strip()
                result.append((number, values))
            return result
        finally:
            workbook.close()
    except (ValueError, KeyError, StopIteration, BadZipFile, OSError) as exc:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            422,
            "Excel格式无效，须含name/phone/password或姓名/手机号/初始密码，最多500行",
        ) from exc


async def employee_import(
    db: AsyncSession, actor: Employee, content: bytes, filename: str
) -> s.EmployeeImportResult:
    rows = await run_in_threadpool(parse_employees, content, filename)
    items = []
    for number, values in rows:
        if "_error" in values:
            items.append(s.ImportRow(row=number, ok=False, message=str(values["_error"])))
            continue
        try:
            payload = s.EmployeeInput.model_validate(values)
        except ValidationError:
            items.append(
                s.ImportRow(row=number, ok=False, message="字段无效，请检查手机号、密码和邮箱")
            )
            continue
        if await repo.optional(db, Employee, Employee.phone == payload.phone):
            items.append(s.ImportRow(row=number, ok=False, message="手机号已存在"))
            continue
        try:
            async with db.begin_nested():
                employee = await shared.create_employee(db, payload)
                await shared.audit(
                    db, actor.id, "employee.import", str(employee.id), {"row": number}
                )
                await db.flush()
                data = await shared.staff_data(db, employee)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            items.append(s.ImportRow(row=number, ok=False, message="手机号重复或记录冲突"))
            continue
        items.append(
            s.ImportRow(row=number, ok=True, message="已创建，首次登录需改密", employee=data)
        )
    return s.EmployeeImportResult(items=items)


def parse_knowledge(content: bytes, filename: str) -> s.KnowledgeUploadRow:
    safe_name = PurePath(filename.replace("\\", "/")).name
    if not safe_name.lower().endswith(".md") or len(content) > 1024 * 1024:
        return s.KnowledgeUploadRow(
            filename=safe_name, valid=False, message="仅支持1MB以内的Markdown文件"
        )
    # Uploaded metadata is a proposal, never authorization to publish or approve.
    file_id = "upload-" + uuid4().hex
    try:
        post = frontmatter.loads(content.decode("utf-8-sig"))
        # Normalize opaque upload IDs; original filenames may be Chinese. Uploaded
        # approval/hash/revision metadata cannot confer publication authority.
        if any(
            type(post.metadata.get(flag, False)) is not bool
            for flag in ("public", "approved", "deleted")
        ):
            raise ValueError("invalid flags")
        post.metadata.pop("hash", None)
        post.metadata.update(file_id=file_id, id=file_id, public=False, approved=False, revision=1)
        if not post.content.strip():
            raise ValueError("empty content")
        document = parse_document(frontmatter.dumps(post), file_id)
        if document["scope"] != "company":
            raise ValueError("company upload only")
        draft = s.KnowledgeUploadDraft(
            file_id=file_id,
            title=document["title"],
            content=document["content"],
            description=document.get("description", ""),
        )
        return s.KnowledgeUploadRow(
            filename=safe_name, valid=True, message="待管理员确认；尚未保存或发布", draft=draft
        )
    except (ValueError, UnicodeError, YAMLError):
        return s.KnowledgeUploadRow(
            filename=safe_name, valid=False, message="文件正文或frontmatter无效"
        )


async def knowledge_upload(files: list[tuple[str, bytes]]) -> s.KnowledgeUploadResult:
    if not 1 <= len(files) <= 20 or sum(len(content) for _, content in files) > MAX_UPLOAD:
        raise AppError(ErrorCode.VALIDATION_ERROR, 413, "每批1至20个文件，合计不超过20MB")
    items = [await run_in_threadpool(parse_knowledge, content, name) for name, content in files]
    return s.KnowledgeUploadResult(items=items)
