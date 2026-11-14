from enum import StrEnum

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import IntegrityError


class ErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    AUTH_LOCKED = "AUTH_LOCKED"
    AUTH_DISABLED = "AUTH_DISABLED"
    PASSWORD_CHANGE_REQUIRED = "PASSWORD_CHANGE_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CARD_NOT_FOUND = "CARD_NOT_FOUND"
    CARD_DISABLED = "CARD_DISABLED"
    LEAD_NOT_FOUND = "LEAD_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    LLM_ERROR = "LLM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    def __init__(self, code: ErrorCode, status: int = 400, message: str | None = None):
        self.code = code
        self.status = status
        self.message = message or code.value
        super().__init__(self.message)


def register_errors(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            {"code": exc.code.value, "message": exc.message}, status_code=exc.status
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"code": "VALIDATION_ERROR", "message": "请检查请求参数"}, status_code=422
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("Database constraint rejected request {}", request.url.path)
        return JSONResponse(
            {"code": "CONFLICT", "message": "数据已存在或仍被使用"}, status_code=409
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled request error type={} path={}", type(exc).__name__, request.url.path
        )
        return JSONResponse(
            {"code": "INTERNAL_ERROR", "message": "服务暂时不可用"}, status_code=500
        )
