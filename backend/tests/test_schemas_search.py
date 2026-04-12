"""Тесты Pydantic-схем поиска."""

from app.schemas.search import ArchiveResponse, SearchResponse


class TestSearchResponse:
    def test_valid(self):
        resp = SearchResponse(total=0, limit=100, offset=0, results=[])
        assert resp.total == 0
        assert resp.results == []


class TestArchiveResponse:
    def test_valid(self):
        resp = ArchiveResponse(total=5, limit=200, offset=0, results=[])
        assert resp.total == 5
        assert resp.limit == 200
