# Operations Runbook

## Backup strategy

### PostgreSQL

- Периодичность: ежедневно ночью (`pg_dump`).
- Ротация: хранить 14 ежедневных копий и 8 недельных.
- Формат: custom dump (`pg_dump -Fc`), чтобы ускорить restore отдельных объектов.

### Файловые выгрузки (exports)

- Источник: таблица `report_records` + API выгрузка.
- Retention policy: `NETOPS_ASSISTANT_EXPORT_RETENTION_DAYS` (по умолчанию 30).
- Операционная практика: по cron чистить устаревшие файлы вне retention окна.

## Restore drill (квартально)

1. Поднять тестовый стенд из чистой БД.
2. Выполнить `alembic upgrade head`.
3. Восстановить dump: `pg_restore`.
4. Проверить login, journal list, reports history, export endpoints.
5. Задокументировать RTO/RPO в отчёте drill.

## Release checklist

1. Все миграции применяются: `alembic upgrade head`.
2. Backend тесты: `pytest`.
3. Smoke проверки API (health/auth/reports/team).
4. Проверка production env (`SECRET_KEY`, LDAP, cookie security, CORS).
5. Релизный тег и changelog.
6. План отката: предыдущий image + предыдущий DB backup.

## Versioning policy

- Семантическое версионирование: `MAJOR.MINOR.PATCH`.
- `PATCH`: bugfix без изменения API контракта.
- `MINOR`: новые backward-compatible фичи.
- `MAJOR`: breaking changes API/данных.
