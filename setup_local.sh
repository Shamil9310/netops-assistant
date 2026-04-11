# Точка входа только для подготовки локального окружения:
# doctor в неинтерактивном режиме, создание зависимостей и настройка проекта без запуска сервисов.

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${ROOT_DIR}/scripts/run_local_app.py" --setup-only "$@"
