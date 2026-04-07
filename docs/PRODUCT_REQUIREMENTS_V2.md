---
title: NetOps Assistant Product Requirements v2
aliases:
  - netops assistant voiced requirements
  - netops assistant product scope
tags:
  - netops-assistant
  - product
  - requirements
created: 2026-04-07
updated: 2026-04-07
---

# NetOps Assistant — Product Requirements v2

## Источник требований
Документ фиксирует требования, проговорённые в ходе обсуждения проекта и уточнённые на основе текущего архива.

## Цель проекта
Собрать внутренний web-сервис, который помогает команде сетевых инженеров:
- фиксировать рабочую активность в течение дня;
- готовить и сопровождать ночные работы;
- использовать шаблоны типовых сетевых изменений;
- автоматически формировать аккуратные отчёты и документы за день, неделю и произвольный период;
- хранить историю работы и документов;
- разграничивать доступ между сотрудниками, руководителем и разработчиком.

## Главные пользовательские сценарии

### 1. Ведение рабочего дня
Пользователь в течение дня добавляет записи:
- номер заявки;
- звонок в TrueConf;
- разговор с коллегами;
- работа в TFS;
- составление плана;
- диагностика и troubleshooting;
- документирование;
- прочие задачи.

Система должна позволять:
- ввести запись быстро;
- указать дату и время;
- указать категорию;
- указать связанный внешний идентификатор;
- сохранить запись;
- потом включить её в отчёт.

### 2. Предварительно запланированные звонки
Пользователь может заранее внести список звонков на нужные даты.

Требование:
- система должна позволять заранее создавать planned events;
- эти события должны автоматически попадать в нужную дату и учитываться при подготовке отчёта;
- после фактического выполнения звонок можно подтвердить, скорректировать или отменить.

### 3. Подготовка ночных работ
Пользователь создаёт документ плана ночных работ.

Система должна уметь хранить:
- заголовок окна;
- дату и время окна;
- общие вводные;
- SR/заявки;
- блоки работ;
- список шагов;
- команды проверки;
- ожидаемый результат;
- rollback;
- пост-действия;
- совместные действия и участников.

### 4. Шаблоны планов
Пользователь не хочет каждый раз писать план с нуля.

Требование:
- должны быть шаблоны типовых работ;
- шаблоны должны подставлять типовую структуру шагов;
- пользователь должен только заменить переменные значения и детали.

### 5. Генерация отчётов
Система должна по команде формировать:
- отчёт за день;
- отчёт за неделю;
- отчёт за период с даты X по дату Y;
- итог по ночным работам;
- отчёт по одному сотруднику;
- отчёт по группе для руководителя.

### 6. Хранение истории
Все записи, планы и отчёты должны храниться в системе.

Требование:
- нужен архив;
- нужен поиск;
- нужна фильтрация по сотруднику, периоду, SR, типу активности, устройству и тегам.

## Ограничения среды

### Безопасность
Пользователь ожидает корпоративные ограничения со стороны ИБ.

Следствия:
- нельзя опираться на произвольные прямые интеграции с внешними системами;
- MVP должен уметь работать полностью как ручной/полуавтоматический контур;
- planned imports и structured input важнее, чем глубокие online-интеграции.

### Развёртывание
Проект будет размещён на одной VM.

Доступный максимум:
- 8 CPU
- 16 GB RAM
- 128 GB disk

### Аутентификация
Цель — LDAP по корпоративной модели, максимально близкой к ожиданиям пользователя и подходу NetBox по идее поведения:
- централизованный login;
- маппинг групп в роли;
- отказ от локальных учёток в production, кроме break-glass/dev режима.

## Ролевая модель

### employee
- видит и редактирует только свои сущности;
- не видит чужие журналы, планы и заметки;
- может выгружать свои отчёты.

### manager
- видит отчёты и активность команды;
- не редактирует записи сотрудников;
- может выгружать отчёты отдельных сотрудников и сводки по группе.

### developer
- имеет технический сервисный контур;
- сопровождает платформу;
- имеет отдельный developer-only dashboard;
- видит системные метрики VM.

## Наблюдаемость и developer dashboard
Нужен отдельный экран только для developer role.

Он должен показывать:
- загрузку CPU;
- использование RAM;
- свободное место на диске;
- состояние backend;
- состояние БД;
- состояние export pipeline;
- ключевые системные ошибки.

На MVP можно реализовать backend-сбор метрик с хоста через локальный агент/`psutil`.

## Доменные сущности v2

### User
- id
- username
- full_name
- role
- is_active
- auth_source
- team_id

### Team
- id
- name
- manager_user_id

### ActivityEntry
- id
- owner_user_id
- activity_type
- source_type
- status
- planned_for
- started_at
- ended_at
- duration_minutes
- external_ref
- title
- description
- tags
- result_text

### PlannedEvent
- id
- owner_user_id
- event_type
- scheduled_start
- scheduled_end
- title
- description
- source_label
- auto_include_in_report
- linked_activity_entry_id

### NightWorkPlan
- id
- owner_user_id
- title
- work_date
- window_start
- window_end
- execution_mode
- global_notes
- post_actions
- status

### NightWorkBlock
- id
- plan_id
- order_no
- sr_number
- title
- summary
- participants
- dependencies
- verification_notes
- rollback_notes
- status

### NightWorkStep
- id
- block_id
- order_no
- step_type
- target_scope
- action_text
- config_text
- check_command
- expected_result
- actual_result
- executor_comment
- status
- executed_at

### PlanTemplate
- id
- key
- name
- category
- description
- template_payload
- is_active

### ReportDocument
- id
- owner_user_id
- report_type
- scope_type
- period_start
- period_end
- content_markdown
- content_plain
- generated_from_payload
- created_at

### ExportFile
- id
- document_id
- export_format
- file_path
- file_size
- checksum
- created_at

### SystemMetricSnapshot
- id
- captured_at
- cpu_percent
- memory_percent
- disk_percent
- load_avg
- service_status_payload

## Основные типы activity_type
- incident
- request
- trueconf_call
- colleague_discussion
- tfs_work
- planning
- documentation
- night_work_execution
- report_preparation
- other

## Основные статусы

### Для ActivityEntry
- planned
- in_progress
- done
- cancelled

### Для NightWorkPlan
- draft
- approved
- in_progress
- completed
- partially_completed
- cancelled

### Для NightWorkStep
- pending
- in_progress
- done
- failed
- skipped
- verification_pending

## Основные экраны
- Сегодня
- Журнал
- Отчёты
- Ночные работы
- Шаблоны
- Архив
- Команда
- Настройки
- Developer Dashboard

## Что не нужно ломать в MVP
- тёмная тема как основной режим;
- быстрый ввод;
- экспорт как обязательный модуль;
- простой запуск на одной VM.

## MVP v2 — минимально правильный объём

### Обязательно
- локальная auth для development + задел под LDAP;
- роли employee / manager / developer;
- CRUD журнала;
- planned events;
- CRUD night work plans;
- CRUD templates;
- дневной и недельный отчёт;
- отчёт за период;
- markdown export;
- archive + search;
- developer metrics page.

### После этого
- DOCX/PDF;
- улучшенный team dashboard;
- audit trail;
- LDAP production mode;
- soft-delete и версии документов.
