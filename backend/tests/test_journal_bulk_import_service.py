"""Тесты массового импорта журнала из текста."""

from __future__ import annotations

from datetime import UTC, date, datetime
from io import BytesIO
from types import SimpleNamespace
from uuid import uuid4

import pytest
from openpyxl import Workbook

from app.services.journal import import_activity_entries_from_excel_workbook
from app.services.journal import import_activity_entries_from_text
from app.services.journal import preview_activity_entries_from_excel_workbook
from app.services.journal import preview_activity_entries_from_text
from app.schemas.journal import BulkJournalImportRequest


class FakeSession:
    def __init__(self) -> None:
        self.added_entries = None

    async def execute(self, _statement):
        class FakeResult:
            def all(self):
                return []

        return FakeResult()

    def add_all(self, entries) -> None:
        self.added_entries = list(entries)

    async def commit(self) -> None:
        return None

    async def refresh(self, entry) -> None:
        return None


@pytest.mark.asyncio
async def test_bulk_import_distributes_entries_by_section_dates() -> None:
    session = FakeSession()
    user = SimpleNamespace(id=uuid4())
    payload = BulkJournalImportRequest(
        text=(
            "Выполненные задачи 10.04.26\n"
            "SR11685598\n"
            "SR11707775\n\n"
            "Выполненные задачи 06.04.26\n"
            "SR11693974\n\n"
            "Взята в работу [Задача 1189236](https://tfs.t2.ru/tfs/Main/Tele2/_workitems/edit/1189236)\n"
        ),
        default_work_date=date(2026, 4, 10),
    )

    created_entries, warnings = await import_activity_entries_from_text(
        session=session,
        user=user,
        payload=payload,
    )

    assert warnings == []
    assert len(created_entries) == 4
    assert session.added_entries is not None
    assert [entry.work_date for entry in session.added_entries] == [
        date(2026, 4, 10),
        date(2026, 4, 10),
        date(2026, 4, 6),
        date(2026, 4, 6),
    ]
    assert [entry.status for entry in session.added_entries] == [
        "closed",
        "closed",
        "closed",
        "in_progress",
    ]
    assert session.added_entries[-1].title == "Задача 1189236"
    assert session.added_entries[-1].ticket_number == "SR1189236"
    assert (
        session.added_entries[-1].task_url
        == "https://tfs.t2.ru/tfs/Main/Tele2/_workitems/edit/1189236"
    )


def test_bulk_import_preview_uses_same_parser() -> None:
    payload = BulkJournalImportRequest(
        text=(
            "Выполненные задачи 09.04.26\n"
            "SR11712210\n\n"
            "Взята в работу [Задача 1189236](https://tfs.t2.ru/tfs/Main/Tele2/_workitems/edit/1189236)\n"
        ),
        default_work_date=date(2026, 4, 10),
    )

    preview_items, warnings = preview_activity_entries_from_text(payload)

    assert warnings == []
    assert [item.work_date for item in preview_items] == [
        date(2026, 4, 9),
        date(2026, 4, 9),
    ]
    assert [item.status for item in preview_items] == ["closed", "in_progress"]


def test_bulk_import_accepts_short_section_names_and_bare_numbers() -> None:
    payload = BulkJournalImportRequest(
        text=("Выполнено\n" "1189236\n\n" "В работе:\n" "Задача 1189237\n"),
        default_work_date=date(2026, 4, 10),
    )

    preview_items, warnings = preview_activity_entries_from_text(payload)

    assert warnings == []
    assert [item.status for item in preview_items] == ["closed", "in_progress"]
    assert [item.title for item in preview_items] == [
        "Задача 1189236",
        "Задача 1189237",
    ]
    assert [item.ticket_number for item in preview_items] == ["SR1189236", "SR1189237"]


def _build_excel_workbook_bytes(rows: list[tuple[object, ...]]) -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Обращение"
    worksheet.append(
        (
            "Номер",
            "Дата регистрации",
            "Тема",
            "Система",
            "Услуга",
            "Группа ответственных",
            "Состояние",
            "Контакт",
            "Параметры",
            "Ответственный",
            "Фактическое разрешение",
        )
    )
    for row in rows:
        worksheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_excel_preview_extracts_ticket_service_and_resolution_date() -> None:
    workbook_bytes = _build_excel_workbook_bytes(
        [
            (
                "SR11692310",
                datetime(2026, 4, 6, 11, 30, 9),
                "Прошу подвести vlan 1747",
                "Департамент Инфраструктуры. Сетевые технологии",
                "Настройка портов сетевого оборудования",
                "Отдел развития и эксплуатации сетевых технологий",
                "Решено",
                "Виноградов Георгий Сергеевич",
                "300.Трудозатрата: 1",
                "Исаев Шамиль Тимурович",
                datetime(2026, 4, 8, 3, 18, 41),
            ),
        ]
    )

    preview_items, warnings = preview_activity_entries_from_excel_workbook(
        workbook_bytes
    )

    assert warnings == []
    assert len(preview_items) == 1
    assert preview_items[0].ticket_number == "SR11692310"
    assert preview_items[0].service == "Настройка портов сетевого оборудования"
    assert preview_items[0].work_date == date(2026, 4, 8)
    assert preview_items[0].status == "closed"
    assert preview_items[0].activity_type == "ticket"


@pytest.mark.asyncio
async def test_excel_import_creates_closed_ticket_entries_with_finish_time() -> None:
    session = FakeSession()
    user = SimpleNamespace(id=uuid4())
    workbook_bytes = _build_excel_workbook_bytes(
        [
            (
                "SR11684788",
                datetime(2026, 4, 3, 14, 14, 54),
                "ACL доступ к Vault",
                "Департамент Инфраструктуры. Сетевые технологии",
                "Правила доступа Access-Lists (ACL) и трансляции адресов NAT",
                "Отдел развития и эксплуатации сетевых технологий",
                "Решено",
                "Роменский Валентин Юрьевич",
                "",
                "Исаев Шамиль Тимурович",
                datetime(2026, 4, 6, 16, 6, 57),
            ),
        ]
    )

    created_entries, warnings = await import_activity_entries_from_excel_workbook(
        session=session,
        user=user,
        workbook_bytes=workbook_bytes,
    )

    assert warnings == []
    assert len(created_entries) == 1
    assert session.added_entries is not None
    assert session.added_entries[0].ticket_number == "SR11684788"
    assert (
        session.added_entries[0].service
        == "Правила доступа Access-Lists (ACL) и трансляции адресов NAT"
    )
    assert session.added_entries[0].work_date == date(2026, 4, 6)
    assert session.added_entries[0].status == "closed"
    assert session.added_entries[0].activity_type == "ticket"
    assert session.added_entries[0].finished_at == datetime(
        2026, 4, 6, 16, 6, 57, tzinfo=UTC
    )


def test_excel_preview_skips_rows_without_resolution_date() -> None:
    workbook_bytes = _build_excel_workbook_bytes(
        [
            (
                "SR11674999",
                datetime(2026, 4, 2, 2, 12, 6),
                "Не работает маршрутизация",
                "Департамент Инфраструктуры. Сетевые технологии",
                "Консультация пользователей по работе сети",
                "Отдел развития и эксплуатации сетевых технологий",
                "Решено",
                "Данилин Александр Сергеевич",
                "",
                "Исаев Шамиль Тимурович",
                None,
            ),
        ]
    )

    preview_items, warnings = preview_activity_entries_from_excel_workbook(
        workbook_bytes
    )

    assert preview_items == []
    assert warnings == ["Строка 2 пропущена: не заполнена дата фактического разрешения"]
