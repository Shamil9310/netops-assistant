"""Тесты вспомогательной логики для шаблонов планов."""

from __future__ import annotations

import pytest

from app.services.template import (
    get_default_template_catalog,
    normalize_template_key,
    validate_template_key,
    validate_template_payload,
)


def test_normalize_template_key_happy_path() -> None:
    """Проверяет нормализацию ключа: обрезка, нижний регистр и замена пробелов."""
    assert normalize_template_key("  BGP Peer Template  ") == "bgp_peer_template"


def test_validate_template_key_rejects_invalid_symbols() -> None:
    """Проверяет, что запрещённые символы приводят к ошибке."""
    with pytest.raises(ValueError):
        validate_template_key("bgp@template")


def test_validate_template_key_rejects_too_short_key() -> None:
    """Проверяет ошибку для слишком короткого ключа."""
    with pytest.raises(ValueError):
        validate_template_key("a")


def test_validate_template_key_happy_path() -> None:
    """Проверяет валидный ключ с разрешёнными символами."""
    assert validate_template_key("BGP:DC4-uplink") == "bgp:dc4-uplink"


def test_validate_template_payload_rejects_invalid_blocks_type() -> None:
    """Проверяет ошибку для неверного типа поля blocks."""
    with pytest.raises(ValueError):
        validate_template_payload({"blocks": {"wrong": "type"}})


def test_validate_template_payload_happy_path() -> None:
    """Проверяет корректные данные шаблона."""
    validate_template_payload(
        {
            "variables": ["site", "neighbor_ip"],
            "blocks": [
                {"title": "Pre-check", "steps": [{"action": "show ip bgp summary"}]},
            ],
        }
    )


def test_default_template_catalog_contains_required_categories() -> None:
    """Проверяет наличие обязательных категорий дефолтных шаблонов."""
    catalog = get_default_template_catalog()
    categories = {str(item["category"]) for item in catalog}
    assert "bgp" in categories
    assert "vlan" in categories
    assert "prefix-list" in categories
    assert "route-map" in categories
    assert "static-route" in categories
    assert "tunnel-cleanup" in categories
    assert "journal" in categories
