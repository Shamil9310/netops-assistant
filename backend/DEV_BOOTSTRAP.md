# Dev Bootstrap — запуск проекта с нуля

## Шаги для локального старта

### 1. Подготовить конфиг
```bash
cp .env.development .env
```

### 2. Запустить PostgreSQL
```bash
docker compose up postgres -d
```

### 3. Применить миграции
```bash
cd backend
alembic upgrade head
```

### 4. Запустить backend
```bash
uvicorn app.main:app --reload
```

При старте `ensure_bootstrap_user` автоматически создаст пользователя из `.env`:
- логин: `NETOPS_ASSISTANT_BOOTSTRAP_USERNAME`
- пароль: `NETOPS_ASSISTANT_BOOTSTRAP_PASSWORD`

## Создать новую миграцию после изменения моделей

```bash
cd backend
alembic revision --autogenerate -m "описание изменений"
# проверить сгенерированный файл в alembic/versions/
alembic upgrade head
```

## Откатить последнюю миграцию

```bash
alembic downgrade -1
```

## Сброс БД в dev (полная пересборка)

```bash
alembic downgrade base
alembic upgrade head
```
