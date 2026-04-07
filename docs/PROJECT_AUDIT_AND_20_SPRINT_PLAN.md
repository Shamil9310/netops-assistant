# NetOps Assistant — audit и execution checklist на 20 спринтов

Дата аудита: 7 апреля 2026

## Как пользоваться файлом

- Отмечай `[x]`, когда завершён конкретный пункт.
- У спринта есть отдельный checkbox `Спринт завершён`.
- Внутри каждого спринта задачи разложены по направлениям: `Backend`, `Frontend`, `DevOps`, `QA/Docs`.
- Поля `Owner`, `Target date`, `Notes` оставлены как рабочие строки для команды.

## Общий статус проекта

- [ ] Проект готов к production
- [x] Есть монорепо `frontend + backend`
- [x] Есть базовый FastAPI backend
- [x] Есть базовый Next.js frontend
- [x] Есть базовая auth-схема через cookie-сессию
- [x] Есть docker-compose для локального запуска
- [ ] Реализован MVP-домен целиком
- [ ] Все ключевые UI-экраны работают на реальных данных
- [ ] Есть миграции БД
- [ ] Есть тестовый контур
- [ ] Есть CI/CD
- [ ] Есть production-ready безопасность
- [ ] Есть observability и эксплуатационный контур

## Короткий итог аудита

### Что уже хорошо

- [x] Репозиторий маленький и понятный
- [x] Backend имеет правильное слоение `api / services / schemas / db / models`
- [x] Frontend уже разделён по основным продуктовым экранам
- [x] Есть рабочий login/logout/me поток
- [x] Есть стартовая документация

### Главные риски

- [ ] В backend отсутствуют основные модули MVP: `journal`, `reports`, `plans`, `export`
- [ ] Основные frontend-страницы опираются на хардкод, а не на реальные данные
- [ ] Используются небезопасные дефолты для `secret_key` и bootstrap-учётки
- [ ] Схема БД создаётся через `create_all()` при запуске приложения
- [ ] Нет Alembic миграций
- [ ] Нет unit/integration/e2e тестов
- [ ] Нет CI/CD и quality gates
- [ ] Нет RBAC, CSRF hardening, audit trail
- [ ] Нет observability
- [ ] Нет production edge-layer и release-процесса

### Быстрые технические заметки

- [x] Backend компилируется через `python3 -m compileall app`
- [ ] Frontend проходит `npm run build`
- [ ] Пересмотреть требование `python >=3.14`

---

## Спринт 1. Stabilization Baseline

Status:
- [ ] Спринт 1 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Убрать небезопасные дефолты из backend config
- [ ] Разделить `development / test / production` конфигурации
- [ ] Вынести bootstrap-пользователя в управляемый dev-only механизм

Frontend:
- [ ] Подготовить единый подход к env-конфигам frontend
- [ ] Зафиксировать базовый стиль обработки ошибок и loading states

DevOps:
- [ ] Добавить линтеры и formatter для backend
- [ ] Добавить линтеры и formatter для frontend
- [ ] Ввести pre-commit hooks

QA/Docs:
- [ ] Зафиксировать MVP scope
- [ ] Описать Definition of Done для задач и спринтов
- [ ] Актуализировать README по запуску

Exit criteria:
- [ ] Есть безопасная конфигурационная база
- [ ] Есть минимальные стандарты качества и разработки

---

## Спринт 2. Database Foundation

Status:
- [ ] Спринт 2 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Подключить Alembic
- [ ] Убрать `create_all()` из startup lifecycle
- [ ] Создать первую миграцию
- [ ] Подготовить начальную схему пользователей и сессий под миграции

Frontend:
- [ ] Подготовить mock/data contracts под будущие реальные API

DevOps:
- [ ] Добавить команду запуска миграций для локальной среды
- [ ] Обновить compose/startup flow под миграции

QA/Docs:
- [ ] Описать процесс миграций в документации
- [ ] Описать процесс локального наполнения тестовыми данными

Exit criteria:
- [ ] Схема БД управляется только через миграции

---

## Спринт 3. Identity and Access

Status:
- [ ] Спринт 3 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Добавить роли `admin / engineer / viewer`
- [ ] Реализовать RBAC на backend
- [ ] Добавить статус блокировки пользователя
- [ ] Добавить аудит логинов и логаутов
- [ ] Усилить session lifecycle и revoke policy

Frontend:
- [ ] Подготовить role-aware navigation
- [ ] Обработать сценарии просроченной или невалидной сессии

DevOps:
- [ ] Подготовить безопасное хранение секретов для окружений

QA/Docs:
- [ ] Описать модель ролей и доступа
- [ ] Подготовить тест-кейсы по auth и role access

Exit criteria:
- [ ] Auth и access model пригодны для внутреннего production

---

## Спринт 4. Journal Domain Model

Status:
- [ ] Спринт 4 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Реализовать модель `JournalEntry`
- [ ] Добавить типы записей
- [ ] Добавить теги и внешние идентификаторы
- [ ] Реализовать repository/service/API слой для журнала
- [ ] Добавить CRUD
- [ ] Добавить пагинацию, фильтры, сортировку

Frontend:
- [ ] Описать типы данных журнала в frontend-контрактах

DevOps:
- [ ] Подготовить миграции под journal domain

QA/Docs:
- [ ] Описать правила заполнения journal entry
- [ ] Подготовить тест-кейсы по CRUD журнала

Exit criteria:
- [ ] Backend поддерживает главный доменный сценарий продукта

---

## Спринт 5. Journal UX v1

Status:
- [ ] Спринт 5 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Доработать API журнала под UX-сценарии

Frontend:
- [ ] Перевести страницу `Журнал` с хардкода на реальный API
- [ ] Реализовать создание записи
- [ ] Реализовать редактирование записи
- [ ] Реализовать удаление записи
- [ ] Добавить быстрый ввод одной строкой
- [ ] Добавить обычную форму ввода
- [ ] Добавить empty/error/loading states

DevOps:
- [ ] Обновить env и API URL документацию при необходимости

QA/Docs:
- [ ] Описать UX сценарии журнала
- [ ] Проверить базовый e2e поток создания записи

Exit criteria:
- [ ] Журнал работает end-to-end

---

## Спринт 6. Today Dashboard Real Data

Status:
- [ ] Спринт 6 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Добавить агрегаты и summary endpoints для dashboard
- [ ] Рассчитать KPI дня и заполненность

Frontend:
- [ ] Перевести экран `Сегодня` на реальные данные
- [ ] Убрать хардкодные timeline и report draft блоки
- [ ] Подключить статистику по категориям

DevOps:
- [ ] Подготовить базовые API smoke-checks для dashboard endpoints

QA/Docs:
- [ ] Описать expected behavior главного экрана

Exit criteria:
- [ ] Экран `Сегодня` стал рабочим оперативным экраном

---

## Спринт 7. Search and Archive

Status:
- [ ] Спринт 7 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Реализовать поиск по журналу
- [ ] Реализовать архивные выборки по датам
- [ ] Добавить фильтры по типам, тегам, external ID
- [ ] Оптимизировать индексы БД для поиска

Frontend:
- [ ] Подключить UI фильтров и поиск в журнале
- [ ] Добавить архивную навигацию по диапазонам дат

DevOps:
- [ ] Проверить запросы и индексы на реальном объёме dev-данных

QA/Docs:
- [ ] Описать ограничения и логику поиска

Exit criteria:
- [ ] Поиск и архив работают стабильно

---

## Спринт 8. Report Engine v1

Status:
- [ ] Спринт 8 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Реализовать модель `Report`
- [ ] Реализовать дневной генератор отчёта
- [ ] Реализовать недельный генератор отчёта
- [ ] Добавить сохранение версий отчётов
- [ ] Определить форматы рендера Markdown/TXT

Frontend:
- [ ] Подготовить frontend contracts для report model

DevOps:
- [ ] Подготовить миграции под reports

QA/Docs:
- [ ] Описать шаблон структуры отчёта
- [ ] Подготовить acceptance checks для report generation

Exit criteria:
- [ ] Отчёты формируются из реальных данных

---

## Спринт 9. Reports UX v1

Status:
- [ ] Спринт 9 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Поддержать preview/save/export сценарии API отчётов

Frontend:
- [ ] Перевести страницу `Отчёты` на реальный backend
- [ ] Добавить выбор периода
- [ ] Добавить предпросмотр
- [ ] Добавить историю генераций
- [ ] Добавить ручную корректировку перед сохранением
- [ ] Добавить copy/export/download actions

DevOps:
- [ ] Подготовить smoke-checks на report API

QA/Docs:
- [ ] Описать пользовательский сценарий работы с отчётами

Exit criteria:
- [ ] Пользователь может собрать и выгрузить отчёт

---

## Спринт 10. Work Plans Domain

Status:
- [ ] Спринт 10 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Реализовать модель `WorkPlan`
- [ ] Реализовать шаблон BGP
- [ ] Реализовать шаблон OSPF
- [ ] Реализовать шаблон VLAN
- [ ] Реализовать шаблон ACL
- [ ] Реализовать генераторы pre-check/config/post-check/rollback
- [ ] Добавить валидацию параметров шаблонов

Frontend:
- [ ] Подготовить contracts для plan templates и plan preview

DevOps:
- [ ] Подготовить миграции под work plans

QA/Docs:
- [ ] Описать структуру плана изменений
- [ ] Зафиксировать acceptance rules для шаблонов

Exit criteria:
- [ ] Есть доменная основа для планов изменений

---

## Спринт 11. Plans UX v1

Status:
- [ ] Спринт 11 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Поддержать API для draft/save/versioning/copy сценариев

Frontend:
- [ ] Перевести страницу `Планы` на реальный API
- [ ] Реализовать создание плана
- [ ] Реализовать редактирование плана
- [ ] Реализовать копирование плана
- [ ] Реализовать версионирование плана
- [ ] Реализовать предпросмотр секций плана
- [ ] Добавить сохранение пользовательских шаблонов и черновиков

DevOps:
- [ ] Подготовить smoke-checks на plan API

QA/Docs:
- [ ] Описать пользовательские сценарии для плана изменений

Exit criteria:
- [ ] Модуль планов работает как основной рабочий инструмент

---

## Спринт 12. Export Subsystem

Status:
- [ ] Спринт 12 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Создать единый export service
- [ ] Довести до production Markdown export
- [ ] Довести до production TXT export
- [ ] Подготовить API-контракт для DOCX/PDF
- [ ] Добавить фоновые задачи для тяжёлого экспорта

Frontend:
- [ ] Подключить реальные export actions в отчётах и планах
- [ ] Показать статусы генерации и скачивания

DevOps:
- [ ] Подготовить инфраструктурную основу под background jobs

QA/Docs:
- [ ] Описать форматы экспорта и ограничения

Exit criteria:
- [ ] Обязательный экспорт MVP работает стабильно

---

## Спринт 13. Quality Gate Expansion

Status:
- [ ] Спринт 13 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Добавить unit-тесты backend
- [ ] Добавить integration-тесты backend

Frontend:
- [ ] Добавить компонентные тесты frontend
- [ ] Добавить smoke e2e тесты

DevOps:
- [ ] Подключить тестовые команды в общий pipeline
- [ ] Зафиксировать минимальные пороги покрытия

QA/Docs:
- [ ] Добавить тестовые фикстуры и фабрики
- [ ] Описать стратегию тестирования

Exit criteria:
- [ ] Есть реальная защита от регрессий

---

## Спринт 14. Observability and Audit

Status:
- [ ] Спринт 14 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Добавить структурированные логи
- [ ] Ввести correlation/request IDs
- [ ] Добавить метрики ошибок и времени ответа
- [ ] Добавить аудит действий пользователя и бизнес-событий

Frontend:
- [ ] Добавить обработку и отображение ключевых системных ошибок

DevOps:
- [ ] Подготовить сбор логов и метрик
- [ ] Подготовить базовые dashboards

QA/Docs:
- [ ] Описать наблюдаемость и аудит-события

Exit criteria:
- [ ] Система наблюдаема и поддерживаема

---

## Спринт 15. CI/CD

Status:
- [ ] Спринт 15 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Подготовить backend build/test/lint stages

Frontend:
- [ ] Подготовить frontend build/test/lint stages

DevOps:
- [ ] Настроить pipeline для lint
- [ ] Настроить pipeline для typecheck
- [ ] Настроить pipeline для test
- [ ] Настроить pipeline для build
- [ ] Собрать контейнерные образы для окружений
- [ ] Добавить миграционный шаг в release flow
- [ ] Подготовить staging-контур

QA/Docs:
- [ ] Описать release flow
- [ ] Описать правила merge и quality gates

Exit criteria:
- [ ] Есть воспроизводимая поставка и автоматическая проверка качества

---

## Спринт 16. Security Hardening

Status:
- [ ] Спринт 16 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Провести threat modeling
- [ ] Добавить CSRF protection для cookie-auth
- [ ] Настроить brute-force protection
- [ ] Усилить audit trail по критичным операциям

Frontend:
- [ ] Поддержать CSRF-safe flow на клиенте
- [ ] Подготовить корректную обработку security failures

DevOps:
- [ ] Настроить security headers
- [ ] Настроить rate limiting
- [ ] Ввести secret management и rotation policy

QA/Docs:
- [ ] Описать security baseline
- [ ] Подготовить security checklist перед релизом

Exit criteria:
- [ ] Закрыты основные уязвимости для внутреннего production

---

## Спринт 17. Performance and Scalability

Status:
- [ ] Спринт 17 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Оптимизировать медленные запросы
- [ ] Проверить индексы
- [ ] Добавить кеширование там, где это оправдано
- [ ] Подготовить Redis и фоновые задачи

Frontend:
- [ ] Снизить лишние запросы и повторные перерисовки критичных экранов

DevOps:
- [ ] Прогнать нагрузочные сценарии
- [ ] Зафиксировать baseline производительности

QA/Docs:
- [ ] Описать performance budget и ограничения

Exit criteria:
- [ ] Система выдерживает ожидаемую рабочую нагрузку

---

## Спринт 18. Admin and Operations

Status:
- [ ] Спринт 18 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Добавить admin endpoints для пользователей и ролей
- [ ] Добавить блокировки пользователей
- [ ] Добавить системные health/readiness/liveness endpoints при необходимости

Frontend:
- [ ] Реализовать базовый admin UI, если он нужен по scope

DevOps:
- [ ] Подготовить резервное копирование
- [ ] Подготовить восстановление
- [ ] Подготовить операционные проверки инфраструктуры

QA/Docs:
- [ ] Описать runbooks
- [ ] Описать on-call/ops процедуры

Exit criteria:
- [ ] Проект операционно управляем

---

## Спринт 19. UAT and Production Readiness

Status:
- [ ] Спринт 19 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Закрыть критичные backend дефекты по итогам UAT

Frontend:
- [ ] Закрыть критичные UX и frontend дефекты по итогам UAT

DevOps:
- [ ] Провести dry-run релиза на staging
- [ ] Подготовить финальный release checklist

QA/Docs:
- [ ] Провести внутреннее UAT с реальными пользователями
- [ ] Зафиксировать и приоритизировать замечания
- [ ] Заморозить scope перед релизом

Exit criteria:
- [ ] Продукт готов к выпуску без критичных рисков

---

## Спринт 20. Release Sprint

Status:
- [ ] Спринт 20 завершён

Meta:
- Owner:
- Target date:
- Notes:

Backend:
- [ ] Выполнить production rollout backend
- [ ] Провести production миграции

Frontend:
- [ ] Выполнить production rollout frontend

DevOps:
- [ ] Провести smoke checks после релиза
- [ ] Настроить и отследить post-release monitoring

QA/Docs:
- [ ] Собрать обратную связь первых пользователей
- [ ] Зафиксировать план post-launch улучшений
- [ ] Закрыть release report

Exit criteria:
- [ ] Проект запущен в рабочую эксплуатацию

---

## Финальный go-live checklist

### Функционально

- [ ] Пользователь может войти в систему с ролевой моделью
- [ ] Можно вести журнал рабочего дня на реальных данных
- [ ] Можно собирать дневные отчёты
- [ ] Можно собирать недельные отчёты
- [ ] Можно создавать и сохранять планы изменений по шаблонам
- [ ] Можно экспортировать обязательные форматы MVP
- [ ] Есть поиск и архив

### Технически

- [ ] Схема БД управляется миграциями
- [ ] Нет критичных хардкодных данных в продуктовых экранах
- [ ] Есть тесты
- [ ] Есть CI/CD
- [ ] Есть staging и production release process

### Безопасность

- [ ] Нет дефолтных небезопасных секретов
- [ ] Cookie/session политика соответствует окружению
- [ ] Есть базовая защита от CSRF и bruteforce
- [ ] Есть аудит действий пользователя по критичным операциям

### Эксплуатация

- [ ] Есть документация для запуска, релиза и восстановления
- [ ] Есть мониторинг и alerting
- [ ] Проведён UAT
- [ ] Устранены критичные замечания перед релизом

## Финальный итог

- [ ] Проект доведён до состояния готового внутреннего production-продукта
- [ ] Основные бизнес-сценарии работают end-to-end
- [ ] Команда может сопровождать продукт без ручного hero-mode
