# Dev Bootstrap — запуск проекта с нуля

## Шаги для локального старта

Если запуск идёт через корневые скрипты `./setup_local.sh` или `./run_local.sh`,
backend-зависимости из `backend/pyproject.toml` ставятся автоматически.
В это входят и зависимости для Excel-импорта, например `openpyxl`
и `python-multipart`.

Команда `./doctor` тоже по умолчанию включает автоустановку недостающих
зависимостей через `--bootstrap-missing`.

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
- логин: `shamil.isaev`
- пароль: `12345678`

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
