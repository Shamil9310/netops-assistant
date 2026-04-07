from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import PlanTemplate

_KEY_PATTERN = re.compile(r"^[a-z0-9:_-]{3,64}$")


def get_default_template_catalog() -> list[dict[str, object]]:
    """Возвращает встроенный каталог типовых шаблонов."""
    return [
        {
            "key": "bgp_peer_change",
            "name": "BGP Peer Change",
            "category": "bgp",
            "description": "Подключение/изменение BGP-соседства",
            "template_payload": {
                "blocks": [
                    {
                        "title": "BGP {{device}} / {{neighbor_ip}}",
                        "description": "Изменение параметров соседа",
                        "sr_number": "{{sr_number}}",
                        "steps": [
                            {"title": "Pre-check", "description": "show bgp summary"},
                            {"title": "Apply config", "description": "neighbor {{neighbor_ip}} remote-as {{remote_as}}"},
                            {"title": "Post-check", "description": "show route / ping", "is_post_action": True},
                        ],
                    }
                ]
            },
            "is_active": True,
        },
        {
            "key": "vlan_change",
            "name": "VLAN Change",
            "category": "vlan",
            "description": "Шаблон изменения VLAN",
            "template_payload": {
                "blocks": [
                    {
                        "title": "VLAN {{vlan_id}} on {{device}}",
                        "description": "Создание/изменение VLAN",
                        "sr_number": "{{sr_number}}",
                        "steps": [
                            {"title": "Pre-check", "description": "show vlan brief"},
                            {"title": "Apply VLAN", "description": "vlan {{vlan_id}}"},
                            {"title": "Post-check", "description": "show mac address-table vlan {{vlan_id}}", "is_post_action": True},
                        ],
                    }
                ]
            },
            "is_active": True,
        },
        {
            "key": "prefix_list_update",
            "name": "Prefix-list Update",
            "category": "prefix-list",
            "description": "Обновление prefix-list",
            "template_payload": {
                "blocks": [
                    {
                        "title": "Prefix-list {{prefix_list_name}}",
                        "description": "Изменение правил маршрутизации",
                        "sr_number": "{{sr_number}}",
                        "steps": [
                            {"title": "Backup config", "description": "show run | section ip prefix-list"},
                            {"title": "Apply rule", "description": "ip prefix-list {{prefix_list_name}} permit {{prefix}}"},
                        ],
                    }
                ]
            },
            "is_active": True,
        },
        {
            "key": "route_map_update",
            "name": "Route-map Update",
            "category": "route-map",
            "description": "Изменение route-map политики",
            "template_payload": {
                "blocks": [
                    {
                        "title": "Route-map {{route_map_name}}",
                        "description": "Корректировка route-map",
                        "sr_number": "{{sr_number}}",
                        "steps": [
                            {"title": "Pre-check", "description": "show route-map {{route_map_name}}"},
                            {"title": "Apply sequence", "description": "route-map {{route_map_name}} permit {{sequence}}"},
                        ],
                    }
                ]
            },
            "is_active": True,
        },
        {
            "key": "static_route_track",
            "name": "Static Route / Track",
            "category": "static-route",
            "description": "Типовой сценарий static route + track",
            "template_payload": {
                "blocks": [
                    {
                        "title": "Static route {{prefix}} via {{next_hop}}",
                        "description": "Добавление маршрута",
                        "sr_number": "{{sr_number}}",
                        "steps": [
                            {"title": "Add route", "description": "ip route {{prefix}} {{next_hop}}"},
                            {"title": "Track check", "description": "show track {{track_id}}", "is_post_action": True},
                        ],
                    }
                ]
            },
            "is_active": True,
        },
        {
            "key": "tunnel_cleanup",
            "name": "Tunnel Cleanup",
            "category": "tunnel-cleanup",
            "description": "План закрытия/очистки туннелей",
            "template_payload": {
                "blocks": [
                    {
                        "title": "Tunnel cleanup {{tunnel_id}}",
                        "description": "Отключение и зачистка туннеля",
                        "sr_number": "{{sr_number}}",
                        "steps": [
                            {"title": "Disable tunnel", "description": "shutdown interface tunnel {{tunnel_id}}"},
                            {"title": "Remove config", "description": "no interface tunnel {{tunnel_id}}"},
                        ],
                    }
                ]
            },
            "is_active": True,
        },
        {
            "key": "journal_incident_entry",
            "name": "Journal Incident Entry",
            "category": "journal",
            "description": "Шаблон типовой записи в дневной журнал по инциденту",
            "template_payload": {
                "entry_template": {
                    "activity_type": "ticket",
                    "status": "open",
                    "title": "Инцидент {{ticket_number}}",
                    "description": "Диагностика инцидента на {{device}}",
                }
            },
            "is_active": True,
        },
    ]


def normalize_template_key(key: str) -> str:
    """Нормализует ключ шаблона для стабильного API-контракта."""
    return key.strip().lower().replace(" ", "_")


def validate_template_key(key: str) -> str:
    """Проверяет формат ключа шаблона и возвращает нормализованное значение."""
    normalized_key = normalize_template_key(key)
    if not _KEY_PATTERN.match(normalized_key):
        raise ValueError(
            "Некорректный ключ шаблона. Допустимы: a-z, 0-9, :, _, -, длина 3..64"
        )
    return normalized_key


def validate_template_payload(payload: dict[str, object]) -> None:
    """Проверяет структуру payload шаблона на базовом уровне."""
    if "blocks" in payload and not isinstance(payload["blocks"], list):
        raise ValueError("Поле blocks в payload должно быть списком")


async def list_templates(
    session: AsyncSession,
    user_id: UUID,
    category: str | None = None,
    is_active: bool | None = None,
) -> list[PlanTemplate]:
    query = select(PlanTemplate).where(PlanTemplate.user_id == user_id).order_by(PlanTemplate.created_at.desc())
    if category is not None:
        query = query.where(PlanTemplate.category == category)
    if is_active is not None:
        query = query.where(PlanTemplate.is_active == is_active)

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_template_by_id(session: AsyncSession, template_id: UUID, user_id: UUID) -> PlanTemplate | None:
    result = await session.execute(
        select(PlanTemplate)
        .where(PlanTemplate.id == template_id)
        .where(PlanTemplate.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_template_by_key(session: AsyncSession, key: str, user_id: UUID) -> PlanTemplate | None:
    result = await session.execute(
        select(PlanTemplate)
        .where(PlanTemplate.key == key)
        .where(PlanTemplate.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_template(
    session: AsyncSession,
    user_id: UUID,
    key: str,
    name: str,
    category: str,
    description: str | None,
    template_payload: dict[str, object],
    is_active: bool,
) -> PlanTemplate:
    normalized_key = validate_template_key(key)
    validate_template_payload(template_payload)

    template = PlanTemplate(
        user_id=user_id,
        key=normalized_key,
        name=name,
        category=category,
        description=description,
        template_payload=template_payload,
        is_active=is_active,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


async def update_template(
    session: AsyncSession,
    template: PlanTemplate,
    key: str | None = None,
    name: str | None = None,
    category: str | None = None,
    description: str | None = None,
    template_payload: dict[str, object] | None = None,
    is_active: bool | None = None,
) -> PlanTemplate:
    if key is not None:
        template.key = validate_template_key(key)
    if name is not None:
        template.name = name
    if category is not None:
        template.category = category
    if description is not None:
        template.description = description
    if template_payload is not None:
        validate_template_payload(template_payload)
        template.template_payload = template_payload
    if is_active is not None:
        template.is_active = is_active

    await session.commit()
    await session.refresh(template)
    return template


async def delete_template(session: AsyncSession, template: PlanTemplate) -> None:
    await session.delete(template)
    await session.commit()


async def import_default_templates(session: AsyncSession, user_id: UUID) -> list[PlanTemplate]:
    """Импортирует дефолтные шаблоны в библиотеку пользователя."""
    imported: list[PlanTemplate] = []
    for default_template in get_default_template_catalog():
        key = str(default_template["key"])
        existing = await get_template_by_key(session, key, user_id)
        if existing is not None:
            continue
        template = PlanTemplate(
            user_id=user_id,
            key=key,
            name=str(default_template["name"]),
            category=str(default_template["category"]),
            description=str(default_template["description"]),
            template_payload=dict(default_template["template_payload"]),
            is_active=bool(default_template["is_active"]),
        )
        session.add(template)
        imported.append(template)

    if imported:
        await session.commit()
        for template in imported:
            await session.refresh(template)
    return imported
