from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import register_errors
from app.modules.workspace.admin_router import router as admin_router
from app.modules.workspace.router import public_redirect, router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await run_in_threadpool(Path(get_settings().upload_root).mkdir, parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(title="AICardHub 本地候选", version="1.0.0", lifespan=lifespan)
register_errors(app)
app.include_router(public_redirect)
app.include_router(router)
app.include_router(admin_router)
app.mount(
    "/files", StaticFiles(directory=get_settings().upload_root, check_dir=False), name="files"
)
