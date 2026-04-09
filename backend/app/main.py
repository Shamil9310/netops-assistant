from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.auth import ensure_bootstrap_user

# Логгер приложения: вместо print() используем единый механизм журналирования.
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Управляет жизненным циклом приложения.

    При старте: создаёт bootstrap-пользователя если его нет.
    Схема БД управляется через Alembic — create_all() здесь не вызывается.
    При остановке: FastAPI сам закрывает соединения.
    """
    logger.info("Старт приложения, окружение: %s", settings.environment)

    # Начальный пользователь нужен для первого входа в систему.
    # Миграции Alembic должны быть применены до старта приложения.
    async with SessionLocal() as session:
        await ensure_bootstrap_user(session)

    logger.info("Bootstrap-пользователь проверен, приложение готово")

    yield

    logger.info("Остановка приложения")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API для NetOps Assistant",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

app.include_router(api_router, prefix="/api/v1")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Добавляет request_id в каждый запрос и ответ.

    Помогает коррелировать записи в логах и ускоряет диагностику ошибок.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled error: request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": request_id},
        )

    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request completed: request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    """Проверяет CSRF для всех state-changing API запросов.

    Используем double-submit cookie:
    - backend выставляет csrf cookie при login;
    - клиент присылает то же значение в `X-CSRF-Token`.
    """
    safe_methods = {"GET", "HEAD", "OPTIONS"}
    exempt_paths = {"/api/v1/auth/login"}
    if request.method in safe_methods or request.url.path in exempt_paths:
        return await call_next(request)

    session_token = request.cookies.get(settings.session_cookie_name)
    if not session_token:
        return await call_next(request)

    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "CSRF validation failed: path=%s request_id=%s",
            request.url.path,
            request_id,
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "CSRF validation failed", "request_id": request_id},
        )

    return await call_next(request)


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    """Возвращает простой ответ для корневого URL приложения."""
    return {"message": "NetOps Assistant API is running"}
