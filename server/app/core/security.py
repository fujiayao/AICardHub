from datetime import timedelta

import bcrypt
import jwt
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import AppError, ErrorCode


async def hash_password(password: str) -> str:
    result = await run_in_threadpool(bcrypt.hashpw, password.encode(), bcrypt.gensalt())
    return result.decode()


async def verify_password(password: str, hashed: str) -> bool:
    return await run_in_threadpool(bcrypt.checkpw, password.encode(), hashed.encode())


def issue_token(subject: str, purpose: str, role: str = "", version: int = 0) -> str:
    hours = 12 if role == "admin" else 24 * (365 if purpose == "visitor" else 30)
    return jwt.encode(
        {
            "sub": subject,
            "purpose": purpose,
            "role": role,
            "version": version,
            "exp": utcnow() + timedelta(hours=hours),
        },
        get_settings().jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str, purpose: str) -> dict[str, object]:
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret.get_secret_value(), algorithms=["HS256"]
        )
    except jwt.PyJWTError as exc:
        raise AppError(ErrorCode.AUTH_REQUIRED, 401, "登录已失效") from exc
    if payload.get("purpose") != purpose:
        raise AppError(ErrorCode.AUTH_REQUIRED, 401, "身份凭据用途不符")
    return dict(payload)
