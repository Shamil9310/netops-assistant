---
title: NetOps Assistant Architecture v2
aliases:
  - netops assistant architecture v2
tags:
  - netops-assistant
  - architecture
  - fastapi
  - nextjs
created: 2026-04-07
updated: 2026-04-07
---

# NetOps Assistant — Architecture v2

## 1. Принципиальная модель системы

Система строится вокруг одного центрального правила:

**запись активности и план работ — первичны, отчёт и документ — вторичны.**

Именно поэтому доменная цепочка должна выглядеть так:

```text
Activity / Planned Event / Night Work Plan
  -> normalization
  -> report/document generation
  -> export
  -> archive/search
```

## 2. Контуры продукта

### 2.1 Дневной контур
Позволяет инженеру быстро фиксировать работу за день.

### 2.2 Контур ночных работ
Позволяет инженеру создавать, вести и закрывать планы ночных работ.

### 2.3 Контур командной отчётности
Позволяет руководителю получать сводки по сотрудникам.

### 2.4 Технический контур разработчика
Позволяет сопровождать платформу и видеть системные метрики.

## 3. Целевая контейнерная схема

```text
Browser
  -> NGINX / reverse proxy
    -> Frontend (Next.js)
    -> Backend API (FastAPI)
      -> PostgreSQL
      -> optional Redis
```

Для MVP на одной VM допустим упрощённый режим без отдельного NGINX контейнера, но в production-контуре reverse proxy нужен.

## 4. Backend architecture

### 4.1 Слои
- `api` — HTTP endpoints
- `schemas` — request/response модели
- `services` — бизнес-логика
- `repositories` — доступ к данным
- `models` — ORM-модели
- `integrations` — LDAP, export helpers, metrics collectors

### 4.2 Модули backend
- `auth`
- `users`
- `teams`
- `journal`
- `planned_events`
- `night_work_plans`
- `templates`
- `reports`
- `export`
- `developer_metrics`
- `audit`

### 4.3 Auth strategy
На development:
- локальная cookie/session auth.

На production:
- LDAP authentication adapter;
- group-to-role mapping;
- локальный break-glass режим только при явном разрешении.

### 4.4 RBAC strategy
Каждый endpoint должен проходить через permission policy.

Примеры:
- employee читает только свои `ActivityEntry` и `NightWorkPlan`;
- manager читает объекты своей команды;
- developer читает service/admin/developer endpoints.

## 5. Frontend architecture

### 5.1 Основные разделы
- dashboard today
- journal
- reports
- night works
- templates
- archive
- team
- developer dashboard

### 5.2 UI philosophy
- тёмная тема по умолчанию;
- data-first layout;
- быстрое добавление записи;
- понятная работа с периодами;
- минимальный когнитивный шум.

### 5.3 State strategy
На старте:
- server components + fetch on server where possible;
- client components only where needed for forms and interactive filters.

Позже:
- query cache layer по реальной необходимости.

## 6. Хранение данных

### 6.1 PostgreSQL как primary storage
Все рабочие сущности живут в PostgreSQL.

### 6.2 Redis
Не является обязательным на первом этапе.
Нужен только если export jobs, scheduling или caching реально потребуют отдельного контура.

### 6.3 File storage
Выгрузки документов и промежуточные файлы:
- локальный storage на VM на MVP;
- с политикой retention;
- с checksum и метаданными.

## 7. Report generation model

### 7.1 Источники для генерации
- activity entries
- planned events
- night work plans
- execution facts

### 7.2 Типы отчётов
- daily
- weekly
- custom range
- night work result
- employee summary
- team summary

### 7.3 Генерация
Сначала в unified markdown model.
Затем export adapters преобразуют его в:
- txt
- md
- docx
- pdf

## 8. Night work plan model

Ночные работы не должны храниться только как один большой текст.

Нужна структура:

```text
NightWorkPlan
  -> NightWorkBlock (SR/change block)
    -> NightWorkStep
```

Каждый step хранит:
- действие;
- где выполняется;
- проверку;
- ожидаемый результат;
- фактический результат;
- статус.

## 9. Template engine model

Шаблон должен быть данными, а не только текстом.

Пример структуры шаблона:

```json
{
  "category": "bgp",
  "name": "Check Point BGP Peer",
  "variables": ["site", "device", "neighbor_ip", "remote_as"],
  "blocks": [
    {
      "title": "Подготовка портов",
      "steps": [
        {"action_text": "Переименовать интерфейсы по техстандарту"}
      ]
    }
  ]
}
```

Это позволит:
- создавать план из шаблона;
- переиспользовать шаги;
- стандартизировать документы.

## 10. Developer dashboard model

Доступен только `developer`.

### Источники данных
- локальный metrics collector;
- health backend;
- статус БД;
- статус export queue.

### Минимальные виджеты
- CPU
- RAM
- disk
- uptime
- backend health
- DB reachability
- recent errors

## 11. Security baseline

- secrets только через env/secret management;
- secure cookies в non-dev окружениях;
- CSRF protection для cookie-based auth;
- audit trail на auth и export;
- soft-delete или versioning для важных документов;
- LDAP over TLS;
- role policy как обязательный middleware/dependency слой.

## 12. Why FastAPI stays a valid choice

FastAPI остаётся нормальным выбором, даже если нужна LDAP-аутентификация.

Причина:
- LDAP сам по себе не привязан к Django;
- можно реализовать отдельный auth adapter на `ldap3`;
- RBAC и session layer всё равно придётся строить под продуктовую модель;
- проект API-first и модульный, что удобно для этого продукта.

## 13. Что нужно изменить по сравнению с текущим архивом

### Обязательно
- пересобрать роли;
- добавить сущности команды;
- добавить planned events;
- добавить полноценный модуль night works;
- добавить templates;
- добавить developer dashboard;
- заменить текущую модель auth на multi-mode skeleton;
- обновить roadmap с 20 до 30 спринтов.

### Технически
- убрать `create_all()` из startup в будущем;
- добавить Alembic;
- устранить проблему API URL для контейнеров;
- разделить internal и public API base URL;
- убрать небезопасные bootstrap defaults из non-dev режима.
