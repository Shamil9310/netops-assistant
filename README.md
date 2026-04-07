# NetOps Assistant

NetOps Assistant — внутренний web-сервис для рабочего дня сетевого инженера.

На старте проект состоит из двух приложений:
- `frontend/` — Next.js интерфейс с основными экранами продукта
- `backend/` — FastAPI API с базовой структурой модулей, health-check и каркасом локальной аутентификации

## Цели MVP

- журнал рабочего дня
- дневные и недельные отчёты
- планы изменений
- архив и поиск
- локальная аутентификация
- обязательная выгрузка отчётов и планов

## Монорепо

```text
netops-assistant-starter/
  backend/
  frontend/
  docker-compose.yml
  README.md
```

## Архитектурные принципы

### Frontend
- Next.js App Router
- TypeScript
- тёмный enterprise UI
- экраны: Сегодня, Журнал, Отчёты, Планы

### Backend
- FastAPI
- Pydantic Settings
- слои `api / services / schemas / db / models`
- префикс API: `/api/v1`

### Данные
- PostgreSQL — основная БД
- Redis — под фоновые задачи и кеш позже

## Что уже есть в этом стартере

### Frontend
- базовый layout
- sidebar навигация
- экран `Сегодня`
- отдельные страницы `Журнал`, `Отчёты`, `Планы`
- интеграция с backend health-check

### Backend
- базовое приложение FastAPI
- router v1
- `/api/v1/health`
- каркас `/api/v1/auth/login`
- настройки через env
- заготовка под SQLAlchemy async engine

## Быстрый старт локально

### Backend

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Docker Compose

```bash
docker compose up --build
```

## Ближайшие шаги

1. подключить реальную БД и Alembic
2. реализовать модели пользователей, ролей и сессий
3. добавить CRUD для journal entries
4. собрать генерацию дневного отчёта
5. добавить экспорт Markdown / TXT
6. после этого перейти к планам изменений и шаблонам
