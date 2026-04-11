# Шпаргалка по командам

Короткий список самых полезных команд для локальной работы.

## Подготовка и запуск

- `./setup_local.sh` - подготовить окружение, создать `.venv`, поставить зависимости.
- `./run_local.sh` - подготовить окружение и запустить backend/frontend.
- `./doctor` - проверить проект и зависимости.

## Через `make`

- `make setup` - то же, что `./setup_local.sh`.
- `make run` - то же, что `./run_local.sh`.
- `make doctor` - то же, что `./doctor`.
- `make test` - полный прогон проекта через `doctor --ci all`.

## Ручные проверки

- `./backend/.venv/bin/python -m pytest -q` - backend-тесты.
- `cd frontend && npm run -s build` - frontend build.

## Когда что запускать

- После чистого клона проекта: `./setup_local.sh`
- Перед началом работы: `./doctor`
- Перед пушем или перед проверкой качества: `make test`
- Если нужен полный локальный запуск: `./run_local.sh`
