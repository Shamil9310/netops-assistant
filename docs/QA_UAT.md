# QA and UAT

## Backend automation baseline

- Unit tests: сервисы journal/reports/night-work/template/auth/security/export.
- Проверка запуска: `cd backend && pytest`.

## Frontend key flows (manual + smoke)

- Login/logout.
- Journal create/edit/delete.
- Reports generate/preview/export (TXT/MD/DOCX/PDF).
- Night work plan create/execute/report.
- Manager team summary and weekly export.

## Smoke checks (pre-release)

1. `GET /api/v1/health`
2. `POST /api/v1/auth/login`
3. `GET /api/v1/dashboard/today`
4. `GET /api/v1/reports/history`
5. `GET /api/v1/team/users/my-team`
6. `GET /api/v1/developer/health`

## UAT сценарии

1. Employee:
   создать активности за день -> сгенерировать daily/weekly/range отчёты -> скачать в 4 форматах.
2. Manager:
   открыть team dashboard -> проверить weekly summary -> выгрузить weekly report сотрудника.
3. Developer:
   открыть developer dashboard -> проверить diagnostics/DB check -> убедиться в наличии request id.
