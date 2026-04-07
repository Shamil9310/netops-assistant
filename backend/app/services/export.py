from __future__ import annotations

import io
import re
import zipfile
from datetime import UTC, datetime, timedelta


def strip_markdown(text: str) -> str:
    """Убирает базовую markdown-разметку для plain text экспорта."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text


def render_docx_bytes(markdown_content: str) -> bytes:
    """Формирует DOCX-файл без внешних зависимостей.

    Мы используем минимальный OpenXML-пакет:
    1) преобразуем markdown в plain text;
    2) кладём строки в word/document.xml как абзацы.
    """
    plain_text = strip_markdown(markdown_content)
    paragraphs_xml = "".join(_docx_paragraph(line) for line in plain_text.splitlines())

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs_xml}</w:body>"
        "</w:document>"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def render_pdf_bytes(markdown_content: str) -> bytes:
    """Формирует простой PDF без внешних библиотек.

    Документ одностраничный и предназначен для быстрого рабочего экспорта.
    Для MVP этого достаточно: текст читается в стандартных PDF readers.
    """
    plain_text = strip_markdown(markdown_content)
    lines = plain_text.splitlines()
    if not lines:
        lines = ["(пустой отчёт)"]

    pdf_lines = ["BT", "/F1 10 Tf", "50 780 Td"]
    for index, line in enumerate(lines[:60]):
        safe = _escape_pdf_text(line)
        if index > 0:
            pdf_lines.append("0 -14 Td")
        pdf_lines.append(f"({safe}) Tj")
    pdf_lines.append("ET")
    content_stream = "\n".join(pdf_lines).encode("utf-8")

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content_stream), content_stream),
    ]

    output = b"%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output += f"{index} 0 obj\n".encode("utf-8") + obj + b"\nendobj\n"

    xref_offset = len(output)
    output += f"xref\n0 {len(objects) + 1}\n".encode("utf-8")
    output += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        output += f"{offset:010d} 00000 n \n".encode("utf-8")
    output += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode("utf-8")
    )
    return output


def calculate_export_expiration(generated_at: datetime, retention_days: int) -> datetime:
    """Возвращает дату истечения хранения выгрузки согласно retention policy."""
    normalized = generated_at if generated_at.tzinfo else generated_at.replace(tzinfo=UTC)
    return normalized + timedelta(days=retention_days)


def _docx_paragraph(text: str) -> str:
    escaped = _escape_xml(text)
    if not escaped:
        return "<w:p/>"
    return f"<w:p><w:r><w:t>{escaped}</w:t></w:r></w:p>"


def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
