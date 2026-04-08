"""Тесты сервиса экспорта: TXT, DOCX, PDF и срок хранения."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services import export as export_service


def test_strip_markdown_removes_basic_formatting() -> None:
    """Проверяет удаление базовой markdown-разметки для TXT экспорта."""
    source = "# Заголовок\n**bold** `code`\n> цитата"
    plain_text = export_service.strip_markdown(source)
    assert "Заголовок" in plain_text
    assert "bold" in plain_text
    assert "code" in plain_text
    assert "цитата" in plain_text
    assert "#" not in plain_text
    assert "**" not in plain_text
    assert "`" not in plain_text


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


def test_calculate_export_expiration_adds_retention_period() -> None:
    """Retention policy: к дате генерации корректно прибавляется количество дней."""
    generated_at = datetime(2026, 4, 7, 10, 0, tzinfo=UTC)
    expires_at = export_service.calculate_export_expiration(generated_at, 30)
    assert expires_at.isoformat() == "2026-05-07T10:00:00+00:00"
