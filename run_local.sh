# Точка входа для полного локального запуска проекта:
# doctor, подготовка окружения, запуск backend и frontend.

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${ROOT_DIR}/scripts/run_local_app.py" "$@"
