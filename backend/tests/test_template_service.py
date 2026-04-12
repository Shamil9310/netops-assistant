"""Тесты чистой логики сервиса шаблонов."""

import pytest

from app.services.template import (
    normalize_template_key,
    validate_template_key,
    validate_template_payload,
    get_default_template_catalog,
)


class TestNormalizeTemplateKey:
    def test_strips_whitespace(self):
        assert normalize_template_key("  bgp_change  ") == "bgp_change"

    def test_converts_to_lowercase(self):
        assert normalize_template_key("BGP_CHANGE") == "bgp_change"

    def test_replaces_spaces_with_underscore(self):
        assert normalize_template_key("bgp change") == "bgp_change"


class TestValidateTemplateKey:
    def test_valid_key(self):
        assert validate_template_key("bgp_peer:change") == "bgp_peer:change"

    def test_too_short(self):
        with pytest.raises(ValueError, match="Некорректный ключ"):
            validate_template_key("ab")

    def test_invalid_chars(self):
        with pytest.raises(ValueError, match="Некорректный ключ"):
            validate_template_key("bgp change!")

    def test_too_long(self):
        with pytest.raises(ValueError, match="Некорректный ключ"):
            validate_template_key("a" * 65)

    def test_normalizes_before_validate(self):
        assert validate_template_key("  BGP_CHANGE  ") == "bgp_change"


class TestValidateTemplatePayload:
    def test_empty_payload_ok(self):
        validate_template_payload({})

    def test_blocks_as_list_ok(self):
        validate_template_payload({"blocks": []})

    def test_blocks_not_list_raises(self):
        with pytest.raises(ValueError, match="должно быть списком"):
            validate_template_payload({"blocks": "not-a-list"})

    def test_extra_fields_ok(self):
        validate_template_payload({"entry_template": {"activity_type": "ticket"}})


class TestGetDefaultTemplateCatalog:
    def test_returns_list(self):
        catalog = get_default_template_catalog()
        assert isinstance(catalog, list)
        assert len(catalog) > 0

    def test_each_template_has_required_fields(self):
        for template in get_default_template_catalog():
            assert "key" in template
            assert "name" in template
            assert "category" in template
            assert "template_payload" in template
            assert "is_active" in template

    def test_all_keys_are_unique(self):
        catalog = get_default_template_catalog()
        keys = [str(t["key"]) for t in catalog]
        assert len(keys) == len(set(keys))
