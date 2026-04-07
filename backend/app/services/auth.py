from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from pwdlib import PasswordHash
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.auth_audit import AuthAuditEvent, AuthAuditEventType
from app.models.user import User, UserRole
from app.models.user_session import UserSession
from app.services.auth_provider import LocalAuthProvider, build_auth_provider

logger = logging.getLogger(__name__)

# Рекомендованный алгоритм хэширования паролей (argon2 по умолчанию в pwdlib).
# Вынесен на уровень модуля — создаём один раз, переиспользуем везде.
_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Хэширует пароль для безопасного хранения в БД."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Проверяет совпадение пароля с хэшем из БД."""
    return _password_hasher.verify(plain_password, stored_hash)


def hash_session_token(raw_token: str) -> str:
    """Хэширует сессионный токен перед сохранением в БД.

    Токен хранится в виде хэша, а не в открытом виде:
    при утечке БД злоумышленник не сможет использовать токены.
    secret_key подмешивается как соль — защита от радужных таблиц.
    """
    return sha256(f"{settings.secret_key}:{raw_token}".encode()).hexdigest()


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    """Возвращает пользователя по имени или None если не найден."""
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def authenticate_user(
    session: AsyncSession,
    username: str,
    password: str,
    client_ip: str | None = None,
) -> User | None:
    """Аутентифицирует пользователя и записывает событие аудита.

    Возвращает User при успехе, None при неверных данных или неактивном аккаунте.
    Всегда записывает аудит-событие — это позволяет обнаружить брутфорс.
    """
    provider = build_auth_provider()
    identity = await provider.authenticate(session, username, password)

    if identity is None and settings.auth_provider == "ldap" and settings.ldap_fallback_to_local:
        logger.warning("LDAP auth неуспешен, пробуем fallback в local provider: username=%s", username)
        local_provider = LocalAuthProvider()
        identity = await local_provider.authenticate(session, username, password)

    if identity is None:
        # Записываем неудачную попытку входа для аудита безопасности.
        await _write_audit_event(
            session,
            event_type=AuthAuditEventType.LOGIN_FAILED,
            username_attempted=username,
            user_id=None,
            client_ip=client_ip,
        )
        await session.commit()
        logger.warning("Неудачная попытка входа: username=%s, ip=%s", username, client_ip)
        return None

    user = await _ensure_user_from_identity(session, identity)
    if user is None or not user.is_active:
        await _write_audit_event(
            session,
            event_type=AuthAuditEventType.LOGIN_FAILED,
            username_attempted=username,
            user_id=None,
            client_ip=client_ip,
        )
        await session.commit()
        logger.warning("Не удалось разрешить user после аутентификации: username=%s", username)
        return None

    await _write_audit_event(
        session,
        event_type=AuthAuditEventType.LOGIN_SUCCESS,
        username_attempted=username,
        user_id=user.id,
        client_ip=client_ip,
    )
    logger.info("Успешный вход: username=%s, ip=%s", username, client_ip)
    return user


async def create_session(session: AsyncSession, user: User) -> str:
    """Создаёт новую сессию для пользователя и возвращает raw token.

    Raw token отдаётся в cookie и никогда не сохраняется в БД —
    только его хэш. Это стандартный паттерн безопасного хранения сессий.
    """
    raw_token = token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)
    db_session = UserSession(
        user_id=user.id,
        token_hash=hash_session_token(raw_token),
        expires_at=expires_at,
    )
    session.add(db_session)
    await session.commit()
    return raw_token


async def revoke_session(session: AsyncSession, raw_token: str, client_ip: str | None = None) -> None:
    """Отзывает сессию (logout) — помечает revoked_at текущим временем.

    Сессия не удаляется из БД для сохранения истории (аудит).
    """
    db_session = await get_active_session(session, raw_token)
    if db_session is None:
        return

    db_session.revoked_at = datetime.now(UTC)

    # Записываем logout в аудит — важно для анализа жизненного цикла сессий.
    if db_session.user_id is not None:
        user = await session.get(User, db_session.user_id)
        username = user.username if user else "unknown"
        await _write_audit_event(
            session,
            event_type=AuthAuditEventType.LOGOUT,
            username_attempted=username,
            user_id=db_session.user_id,
            client_ip=client_ip,
        )

    await session.commit()
    logger.info("Logout: user_id=%s, ip=%s", db_session.user_id, client_ip)


async def get_active_session(session: AsyncSession, raw_token: str) -> UserSession | None:
    """Возвращает активную (не истёкшую, не отозванную) сессию по raw token."""
    now = datetime.now(UTC)
    statement: Select[tuple[UserSession]] = (
        select(UserSession)
        .options(selectinload(UserSession.user))
        .where(UserSession.token_hash == hash_session_token(raw_token))
        .where(UserSession.revoked_at.is_(None))
        .where(UserSession.expires_at > now)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_current_user(session: AsyncSession, raw_token: str | None) -> User | None:
    """Возвращает текущего активного пользователя по token из cookie.

    Используется как FastAPI dependency и в SSR-запросах с фронтенда.
    """
    if not raw_token:
        return None
    db_session = await get_active_session(session, raw_token)
    if db_session is None or db_session.user is None or not db_session.user.is_active:
        return None
    return db_session.user


async def ensure_bootstrap_user(session: AsyncSession) -> None:
    """Создаёт начального пользователя при первом запуске, если его ещё нет.

    Bootstrap-пользователь нужен для первого входа в систему после развёртывания.
    В production рекомендуется сменить пароль сразу после первого входа.
    """
    existing_user = await get_user_by_username(session, settings.bootstrap_username)
    if existing_user is not None:
        return

    # Bootstrap-пользователь получает роль DEVELOPER — он технический администратор.
    session.add(
        User(
            username=settings.bootstrap_username,
            full_name=settings.bootstrap_full_name,
            password_hash=hash_password(settings.bootstrap_password),
            is_active=True,
            role=UserRole.DEVELOPER.value,
        )
    )
    await session.commit()
    logger.info("Bootstrap-пользователь создан: username=%s", settings.bootstrap_username)


async def _ensure_user_from_identity(
    session: AsyncSession,
    identity: object,
) -> User | None:
    """Создаёт или обновляет локального пользователя по результату provider-аутентификации.

    Для LDAP это точка синхронизации корпоративного пользователя в локальную БД.
    Для local provider обновлений обычно не требуется, но функция остаётся общей.
    """
    username = getattr(identity, "username", "")
    full_name = getattr(identity, "full_name", "")
    role = getattr(identity, "role", UserRole.EMPLOYEE.value)

    if not username:
        return None
    if role not in {role_item.value for role_item in UserRole}:
        role = UserRole.EMPLOYEE.value

    user = await get_user_by_username(session, username)
    if user is None:
        user = User(
            username=username,
            full_name=full_name or username,
            password_hash=hash_password(token_urlsafe(32)),
            is_active=True,
            role=role,
        )
        session.add(user)
        await session.flush()
        return user

    updated = False
    if full_name and user.full_name != full_name:
        user.full_name = full_name
        updated = True
    if user.role != role:
        user.role = role
        updated = True
    if not user.is_active:
        user.is_active = True
        updated = True
    if updated:
        await session.flush()
    return user


async def _write_audit_event(
    session: AsyncSession,
    event_type: AuthAuditEventType,
    username_attempted: str,
    user_id: object | None,
    client_ip: str | None,
) -> None:
    """Записывает событие аудита в БД.

    Вынесено в приватный метод, чтобы не дублировать код в каждой функции.
    Не вызывает commit — вызывающий код делает это сам после основной операции.
    """
    session.add(
        AuthAuditEvent(
            event_type=event_type.value,
            username_attempted=username_attempted,
            user_id=user_id,
            client_ip=client_ip,
        )
    )
