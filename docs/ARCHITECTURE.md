# NetOps Assistant — Architecture v0.1

## Контур продукта

NetOps Assistant строится как внутренний web-сервис для сетевого инженера.

Основные сценарии:
- ведение журнала рабочего дня;
- сборка дневных и недельных отчётов;
- подготовка планов изменений;
- хранение истории и поиск;
- обязательная выгрузка отчётов и планов.

## Контейнерная схема

```text
Browser
  -> NGINX
    -> Frontend (Next.js)
    -> Backend API (FastAPI)
      -> PostgreSQL
      -> Redis
```

В стартере NGINX ещё не добавлен как отдельный контейнер. На первом шаге достаточно прямого запуска frontend и backend. Его нужно будет ввести перед развёртыванием на рабочем сервере.

## Frontend

### Технологии
- Next.js
- TypeScript
- App Router
- тёмный enterprise UI

### Экранная модель MVP
- Сегодня
- Журнал
- Отчёты
- Планы
- позже: Архив, Шаблоны, Настройки

### Ответственность frontend
- отображение данных;
- быстрый ввод;
- предпросмотр отчётов;
- предпросмотр плана работ;
- запуск экспорта.

## Backend

### Технологии
- FastAPI
- Pydantic Settings
- SQLAlchemy asyncio
- PostgreSQL

### Слои
- `api` — HTTP endpoints
- `schemas` — request/response модели
- `services` — бизнес-логика
- `db` — engine, sessions, repositories позже
- `models` — доменные и ORM-модели

### Базовые модули backend
- auth
- health
- journal
- reports
- plans
- export

В стартере реализованы только `health` и каркас `auth`.

## Данные MVP

### Пользователь
- id
- username
- password_hash
- role
- is_active

### JournalEntry
- id
- entry_type
- started_at
- ended_at
- duration_minutes
- external_id
- title
- description
- tags
- created_by

### WorkPlan
- id
- template_key
- work_order_id
- payload
- precheck_text
- config_text
- postcheck_text
- rollback_text

### Report
- id
- report_type
- period_start
- period_end
- content_markdown
- content_plain
- created_by

## Роли
- `admin` — полный доступ
- `engineer` — основная рабочая роль
- `viewer` — только просмотр

## Экспорт

Экспорт является обязательным модулем, а не дополнительной функцией.

### Обязательные форматы MVP
- Markdown
- TXT
- copy to clipboard

### Следующие форматы
- DOCX
- PDF
- CSV/XLSX для журналов и выборок

## Ближайший план кодинга

### Шаг 1
- модели пользователей и ролей;
- реальная локальная аутентификация;
- cookie-based session или JWT-схема.

### Шаг 2
- CRUD для journal entries;
- быстрый ввод одной строкой;
- группировка по дням.

### Шаг 3
- генератор дневного отчёта;
- генератор недельного отчёта;
- экспорт Markdown/TXT.

### Шаг 4
- модуль планов изменений;
- шаблоны BGP / OSPF / VLAN / ACL;
- экспорт плана.
