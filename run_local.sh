#!/usr/bin/env bash
set -euo pipefail

# Полный локальный запуск проекта одной командой:
# 1) выполняет setup_local.sh (зависимости + .env + миграции),
# 2) запускает backend и frontend параллельно,
# 3) проверяет, что backend действительно поднялся и отвечает на healthcheck,
# 4) останавливает оба процесса по Ctrl+C.
#
# Важное отличие от предыдущей версии:
# скрипт больше не считает проект "запущенным" сразу после старта процессов.
# Сначала он убеждается, что backend действительно жив и отвечает,
# а frontend занял свой порт. Это сильно упрощает диагностику.

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
RUNTIME_DIR="${ROOT_DIR}/.dev_runtime/run_local"

BACKEND_PID=""
FRONTEND_PID=""
BACKEND_LOG="${RUNTIME_DIR}/backend.log"
FRONTEND_LOG="${RUNTIME_DIR}/frontend.log"

mkdir -p "${RUNTIME_DIR}"

get_pid_command() {
  local pid="$1"
  ps -p "${pid}" -o command= 2>/dev/null || true
}

is_pid_alive() {
  local pid="$1"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

print_log_tail() {
  local file_path="$1"
  local title="$2"

  if [[ -f "${file_path}" ]]; then
    echo ""
    echo "[run_local] ===== ${title} ====="
    tail -n 40 "${file_path}" || true
    echo "[run_local] ====================="
    echo ""
  fi
}

free_port_or_fail() {
  local port="$1"
  local pids

  pids="$(lsof -tiTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "${pids}" ]]; then
    return 0
  fi

  echo "[run_local] Порт ${port} занят, принудительно завершаю процессы: ${pids}"
  for pid in ${pids}; do
    local command
    command="$(get_pid_command "${pid}")"
    echo "[run_local] kill -9 ${pid} (${command})"
    kill -9 "${pid}" 2>/dev/null || true
  done

  sleep 1

  # После завершения процессов повторно проверяем порт.
  # Если он всё ещё занят, лучше остановить запуск сразу,
  # чем создавать ложное ощущение, что приложение поднялось.
  if lsof -tiTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "[run_local] Ошибка: порт ${port} всё ещё занят после попытки освобождения."
    exit 1
  fi
}

wait_for_http() {
  local url="$1"
  local process_pid="$2"
  local component_name="$3"
  local log_file="$4"
  local max_attempts="${5:-60}"
  local attempt=1

  while (( attempt <= max_attempts )); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      echo "[run_local] ${component_name} готов: ${url}"
      return 0
    fi

    if ! is_pid_alive "${process_pid}"; then
      echo "[run_local] Ошибка: ${component_name} завершился раньше, чем стал доступен."
      print_log_tail "${log_file}" "${component_name} log tail"
      exit 1
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  echo "[run_local] Ошибка: ${component_name} не стал доступен за ${max_attempts} секунд."
  print_log_tail "${log_file}" "${component_name} log tail"
  exit 1
}

wait_for_port() {
  local port="$1"
  local process_pid="$2"
  local component_name="$3"
  local log_file="$4"
  local max_attempts="${5:-60}"
  local attempt=1

  while (( attempt <= max_attempts )); do
    if lsof -tiTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "[run_local] ${component_name} слушает порт ${port}"
      return 0
    fi

    if ! is_pid_alive "${process_pid}"; then
      echo "[run_local] Ошибка: ${component_name} завершился раньше, чем занял порт ${port}."
      print_log_tail "${log_file}" "${component_name} log tail"
      exit 1
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  echo "[run_local] Ошибка: ${component_name} не занял порт ${port} за ${max_attempts} секунд."
  print_log_tail "${log_file}" "${component_name} log tail"
  exit 1
}

cleanup() {
  echo ""
  echo "[run_local] Останавливаю процессы..."

  if is_pid_alive "${BACKEND_PID}"; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi

  if is_pid_alive "${FRONTEND_PID}"; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi

  wait || true
  echo "[run_local] Остановлено."
}

trap cleanup INT TERM EXIT

: > "${BACKEND_LOG}"
: > "${FRONTEND_LOG}"

echo "[run_local] Подготавливаю окружение..."
"${ROOT_DIR}/setup_local.sh"

free_port_or_fail 8000
free_port_or_fail 3000

echo "[run_local] Запускаю backend..."
(
  cd "${BACKEND_DIR}"
  source .venv/bin/activate
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) > "${BACKEND_LOG}" 2>&1 &
BACKEND_PID=$!

wait_for_http "http://localhost:8000/api/v1/health" "${BACKEND_PID}" "Backend" "${BACKEND_LOG}" 60

echo "[run_local] Запускаю frontend..."
(
  cd "${FRONTEND_DIR}"
  npm run dev -- --port 3000
) > "${FRONTEND_LOG}" 2>&1 &
FRONTEND_PID=$!

wait_for_port 3000 "${FRONTEND_PID}" "Frontend" "${FRONTEND_LOG}" 60

echo ""
echo "[run_local] Приложение запущено:"
echo "  Frontend: http://localhost:3000"
echo "  Backend : http://localhost:8000"
echo "  Логин   : engineer"
echo "  Пароль  : engineer123"
echo "  Логи    : ${RUNTIME_DIR}"
echo ""
echo "[run_local] Для остановки нажми Ctrl+C"

wait
