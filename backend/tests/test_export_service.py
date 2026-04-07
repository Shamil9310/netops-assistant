"""Тесты export pipeline v2: TXT/DOCX/PDF и retention rules."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services import export as export_service


def test_strip_markdown_happy_path() -> None:
    """Проверяет удаление базовой markdown-разметки для TXT экспорта."""
    source = "# Заголовок\n**bold** `code`\n> цитата"
    result = export_service.strip_markdown(source)
    assert "Заголовок" in result
    assert "bold" in result
    assert "code" in result
    assert "цитата" in result
    assert "#" not in result
    assert "**" not in result
    assert "`" not in result


def test_render_docx_bytes_returns_zip_signature() -> None:
    """DOCX должен возвращаться как zip-пакет (сигнатура PK)."""
    content = export_service.render_docx_bytes("# Отчёт\nТест")
    assert isinstance(content, bytes)
    assert content.startswith(b"PK")


def test_render_pdf_bytes_returns_pdf_signature() -> None:
    """PDF должен начинаться с заголовка формата %PDF."""
    content = export_service.render_pdf_bytes("# Отчёт\nТест")
    assert isinstance(content, bytes)
    assert content.startswith(b"%PDF")


def test_calculate_export_expiration_happy_path() -> None:
    """Retention policy: к дате генерации корректно прибавляется количество дней."""
    generated_at = datetime(2026, 4, 7, 10, 0, tzinfo=UTC)
    expires_at = export_service.calculate_export_expiration(generated_at, 30)
    assert expires_at.isoformat() == "2026-05-07T10:00:00+00:00"
