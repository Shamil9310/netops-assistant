"""Тесты чистой логики сервиса поиска."""

import pytest
from datetime import datetime, UTC

from app.services.search import (
    _normalize_search_query,
    _validate_search_arguments,
)


class TestNormalizeSearchQuery:
    def test_none_returns_none(self):
        assert _normalize_search_query(None) is None

    def test_empty_string_returns_none(self):
        assert _normalize_search_query("") is None

    def test_whitespace_only_returns_none(self):
        assert _normalize_search_query("   ") is None

    def test_strips_whitespace(self):
        assert _normalize_search_query("  bgp  ") == "bgp"

    def test_returns_text(self):
        assert _normalize_search_query("bgp") == "bgp"


class TestValidateSearchArguments:
    def test_valid_args(self):
        _validate_search_arguments(None, None, 100, 0)

    def test_date_from_after_date_to_raises(self):
        now = datetime.now(UTC)
        past = datetime(2020, 1, 1, tzinfo=UTC)
        with pytest.raises(ValueError, match="date_from не может быть позже"):
            _validate_search_arguments(now, past, 100, 0)

    def test_zero_limit_raises(self):
        with pytest.raises(ValueError, match="limit должен быть больше 0"):
            _validate_search_arguments(None, None, 0, 0)

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError):
            _validate_search_arguments(None, None, -1, 0)

    def test_negative_offset_raises(self):
        with pytest.raises(ValueError, match="offset не может быть отрицательным"):
            _validate_search_arguments(None, None, 100, -1)

    def test_equal_date_range_ok(self):
        same = datetime(2024, 1, 1, tzinfo=UTC)
        _validate_search_arguments(same, same, 100, 0)
