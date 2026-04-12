"""Тесты Pydantic-схем шаблонов."""

import pytest
from pydantic import ValidationError

from app.schemas.template import PlanTemplateCreateRequest, PlanTemplateUpdateRequest


class TestPlanTemplateCreateRequest:
    def test_valid(self):
        req = PlanTemplateCreateRequest(
            key="bgp_change",
            name="BGP Change",
            category="bgp",
        )
        assert req.key == "bgp_change"
        assert req.is_active is True
        assert req.template_payload == {}

    def test_key_too_short(self):
        with pytest.raises(ValidationError):
            PlanTemplateCreateRequest(key="ab", name="Test", category="cat")

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            PlanTemplateCreateRequest(key="key_ok", name="T", category="cat")

    def test_category_too_short(self):
        with pytest.raises(ValidationError):
            PlanTemplateCreateRequest(key="key_ok", name="Name Ok", category="c")

    def test_with_payload(self):
        req = PlanTemplateCreateRequest(
            key="vlan_change",
            name="VLAN Change",
            category="vlan",
            template_payload={"blocks": []},
        )
        assert req.template_payload == {"blocks": []}


class TestPlanTemplateUpdateRequest:
    def test_all_optional(self):
        req = PlanTemplateUpdateRequest()
        assert req.key is None
        assert req.name is None
        assert req.is_active is None

    def test_partial_update(self):
        req = PlanTemplateUpdateRequest(name="New Name", is_active=False)
        assert req.name == "New Name"
        assert req.is_active is False
        assert req.key is None
