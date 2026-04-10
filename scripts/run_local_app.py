#!/usr/bin/env python3
"""Единый сценарий локальной подготовки и запуска проекта.

Этот файл является центральной точкой логики для двух shell-скриптов:
- run_local.sh запускает полный локальный сценарий;
- setup_local.sh выполняет только подготовку окружения без старта сервисов.
"""

from __future__ import annotations

import argparse
import os
import secrets
import signal
import socket
import subprocess
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
RUNTIME_DIR = ROOT_DIR / ".dev_runtime" / "run_local"
BACKEND_LOG = RUNTIME_DIR / "backend.log"
FRONTEND_LOG = RUNTIME_DIR / "frontend.log"
BACKEND_URL = "http://localhost:8000/api/v1/health"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
DB_NAME = "netops_assistant"

BACKEND_PROCESS: subprocess.Popen[str] | None = None
FRONTEND_PROCESS: subprocess.Popen[str] | None = None
STOPPING = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Полный локальный запуск проекта с проверкой готовности backend/frontend.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Сколько секунд ждать готовности backend/frontend.",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Не выполнять подготовку окружения перед запуском.",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Только подготовить окружение и завершиться без запуска сервисов.",
    )
    parser.add_argument(
        "--skip-doctor",
        action="store_true",
        help="Не запускать doctor перед подготовкой и стартом приложения.",
    )
    return parser.parse_args()


def print_line(message: str) -> None:
    print(f"[run_local] {message}")


def run_command(
    command: list[str],
    cwd: Path = ROOT_DIR,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or "без вывода"
        raise RuntimeError(
            f"Команда завершилась с кодом {result.returncode}: {' '.join(command)}\n{details}"
        )
    return result


def read_pid_command(pid: int) -> str:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip()


def is_process_alive(process: subprocess.Popen[str] | None) -> bool:
    return process is not None and process.poll() is None


def print_log_tail(file_path: Path, title: str, lines: int = 40) -> None:
    if not file_path.exists():
        return

    print()
    print(f"[run_local] ===== {title} =====")
    content = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in content[-lines:]:
        print(line)
    print("[run_local] =====================")
    print()


def find_listening_pids(port: int) -> list[int]:
    result = subprocess.run(
        ["lsof", f"-tiTCP:{port}", "-sTCP:LISTEN"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(f"Не удалось проверить порт {port}: {result.stderr.strip()}")

    pids: list[int] = []
    for line in result.stdout.splitlines():
        value = line.strip()
        if value.isdigit():
            pids.append(int(value))
    return pids


def free_port_or_fail(port: int) -> None:
    pids = find_listening_pids(port)
    if not pids:
        return

    joined = " ".join(str(pid) for pid in pids)
    print_line(f"Порт {port} занят, принудительно завершаю процессы: {joined}")
    for pid in pids:
        command = read_pid_command(pid)
        print_line(f"kill -9 {pid} ({command})")
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            continue

    time.sleep(1)
    if find_listening_pids(port):
        raise RuntimeError(f"Порт {port} всё ещё занят после попытки освобождения.")


def wait_for_http(
    url: str,
    process: subprocess.Popen[str],
    component_name: str,
    log_file: Path,
    timeout_sec: int,
) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if 200 <= response.status < 400:
                    print_line(f"{component_name} готов: {url}")
                    return
        except (urllib.error.URLError, TimeoutError, socket.timeout):
            pass

        if process.poll() is not None:
            print_line(
                f"Ошибка: {component_name} завершился раньше, чем стал доступен."
            )
            print_log_tail(log_file, f"{component_name} log tail")
            raise RuntimeError(f"{component_name} не запустился")

        time.sleep(1)

    print_line(f"Ошибка: {component_name} не стал доступен за {timeout_sec} секунд.")
    print_log_tail(log_file, f"{component_name} log tail")
    raise RuntimeError(f"{component_name} не стал доступен")


def wait_for_port(
    port: int,
    process: subprocess.Popen[str],
    component_name: str,
    log_file: Path,
    timeout_sec: int,
) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if find_listening_pids(port):
            print_line(f"{component_name} слушает порт {port}")
            return

        if process.poll() is not None:
            print_line(
                f"Ошибка: {component_name} завершился раньше, чем занял порт {port}."
            )
            print_log_tail(log_file, f"{component_name} log tail")
            raise RuntimeError(f"{component_name} не занял порт")

        time.sleep(1)

    print_line(
        f"Ошибка: {component_name} не занял порт {port} за {timeout_sec} секунд."
    )
    print_log_tail(log_file, f"{component_name} log tail")
    raise RuntimeError(f"{component_name} не занял порт")


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return


def cleanup() -> None:
    global STOPPING
    if STOPPING:
        return
    STOPPING = True

    print()
    print_line("Останавливаю процессы...")
    stop_process(BACKEND_PROCESS)
    stop_process(FRONTEND_PROCESS)

    for process in (BACKEND_PROCESS, FRONTEND_PROCESS):
        if process is None:
            continue
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                continue

    print_line("Остановлено.")


def signal_handler(signum: int, _frame: object | None) -> None:
    cleanup()
    raise SystemExit(128 + signum)


def require_command(command: str, install_hint: str) -> str:
    path = shutil.which(command)
    if path is None:
        raise RuntimeError(f"Не найдена команда `{command}`. {install_hint}")
    return path


def ensure_homebrew() -> None:
    brew_path = shutil.which("brew")
    if brew_path is None:
        raise RuntimeError("Homebrew не найден. Установи его с https://brew.sh")
    print_line(f"Homebrew найден: {brew_path}")


def ensure_postgres() -> None:
    if shutil.which("psql") is None:
        print_line("PostgreSQL не найден, устанавливаю через brew...")
        run_command(["brew", "install", "postgresql@17"])
        run_command(["brew", "services", "start", "postgresql@17"])
        time.sleep(2)
        return

    version = run_command(["psql", "--version"]).stdout.strip()
    print_line(f"PostgreSQL найден: {version}")

    pg_isready = shutil.which("pg_isready")
    if pg_isready is not None:
        ready = subprocess.run([pg_isready, "-q"], check=False).returncode == 0
        if not ready:
            print_line("PostgreSQL не запущен, запускаю через brew services...")
            started = subprocess.run(
                ["brew", "services", "start", "postgresql@17"],
                text=True,
                capture_output=True,
                check=False,
            )
            if started.returncode != 0:
                run_command(["brew", "services", "start", "postgresql"])
            time.sleep(2)


def ensure_database() -> None:
    result = run_command(["psql", "-lqt"], check=False)
    databases = [line.split("|", 1)[0].strip() for line in result.stdout.splitlines()]
    if DB_NAME in databases:
        print_line(f"База данных `{DB_NAME}` уже существует")
        return

    run_command(["createdb", DB_NAME])
    print_line(f"База данных `{DB_NAME}` создана")


def ensure_python() -> str:
    python_path = require_command(
        "python3", "Установи Python 3, например через `brew install python`."
    )
    version = run_command([python_path, "--version"]).stdout.strip()
    print_line(f"Python найден: {version}")
    return python_path


def ensure_root_venv(python_bin: str) -> str:
    venv_dir = ROOT_DIR / ".venv"
    if not venv_dir.exists():
        run_command([python_bin, "-m", "venv", str(venv_dir)])
        print_line("Создано корневое виртуальное окружение проекта")
    else:
        print_line("Корневое виртуальное окружение проекта уже существует")
    return str(venv_dir / "bin" / "python")


def ensure_backend_dependencies(venv_python: str) -> None:
    run_command([venv_python, "-m", "pip", "install", "-e", "."], cwd=BACKEND_DIR)
    print_line("Backend зависимости установлены")


def ensure_backend_env() -> None:
    env_path = BACKEND_DIR / ".env"
    if env_path.exists():
        print_line("Backend .env уже существует")
        return

    template = (BACKEND_DIR / ".env.example").read_text(encoding="utf-8")
    current_user = (
        os.environ.get("USER") or run_command(["whoami"]).stdout.strip() or "netops"
    )
    database_url = f"postgresql+asyncpg://{current_user}@localhost:5432/{DB_NAME}"
    updated = template.replace(
        "postgresql+asyncpg://netops:netops@localhost:5432/netops_assistant",
        database_url,
    )
    updated = updated.replace("dev-only-change-me", secrets.token_hex(32), 1)
    env_path.write_text(updated, encoding="utf-8")
    print_line("Backend .env создан")


def run_alembic_migrations(venv_python: str) -> None:
    env = os.environ.copy()
    env["PATH"] = f"{ROOT_DIR / '.venv' / 'bin'}:{env.get('PATH', '')}"
    run_command(
        [venv_python, "-m", "alembic", "upgrade", "head"], cwd=BACKEND_DIR, env=env
    )
    print_line("Миграции Alembic применены")


def ensure_node() -> None:
    node_path = require_command(
        "node", "Установи Node.js, например через `brew install node`."
    )
    version = run_command([node_path, "--version"]).stdout.strip()
    print_line(f"Node.js найден: {version}")


def ensure_frontend_dependencies() -> None:
    run_command(["npm", "install"], cwd=FRONTEND_DIR)
    print_line("Frontend зависимости установлены")


def ensure_frontend_env() -> None:
    env_path = FRONTEND_DIR / ".env.local"
    if env_path.exists():
        print_line("Frontend .env.local уже существует")
        return

    template = (FRONTEND_DIR / ".env.example").read_text(encoding="utf-8")
    env_path.write_text(template, encoding="utf-8")
    print_line("Frontend .env.local создан")


def run_doctor(setup_only: bool = False) -> None:
    doctor_command = [sys.executable, str(ROOT_DIR / "doctor.py")]
    if setup_only:
        print_line(
            "Запускаю doctor перед подготовкой в неинтерактивном режиме: выполняю all и завершаюсь..."
        )
        doctor_command.extend(["--ci", "all"])
    else:
        print_line(
            "Запускаю doctor перед подготовкой и стартом в неинтерактивном режиме: выполняю all с autofix..."
        )
        doctor_command.extend(["--ci", "all", "--autofix"])

    result = subprocess.run(
        doctor_command,
        cwd=ROOT_DIR,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("doctor завершился с ошибкой. Локальный запуск остановлен.")
    print_line("doctor завершился успешно")


def run_setup() -> None:
    print_line("Подготавливаю окружение...")
    ensure_homebrew()
    ensure_postgres()
    ensure_database()
    python_bin = ensure_python()
    venv_python = ensure_root_venv(python_bin)
    ensure_backend_dependencies(venv_python)
    ensure_backend_env()
    run_alembic_migrations(venv_python)
    ensure_node()
    ensure_frontend_dependencies()
    ensure_frontend_env()


def start_backend() -> subprocess.Popen[str]:
    log_handle = BACKEND_LOG.open("w", encoding="utf-8")
    uvicorn_bin = ROOT_DIR / ".venv" / "bin" / "uvicorn"
    if not uvicorn_bin.exists():
        raise RuntimeError(
            "Не найден .venv/bin/uvicorn. setup_local.sh должен создать окружение."
        )

    print_line("Запускаю backend...")
    return subprocess.Popen(
        [
            str(uvicorn_bin),
            "app.main:app",
            "--reload",
            "--host",
            "0.0.0.0",
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=BACKEND_DIR,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )


def start_frontend() -> subprocess.Popen[str]:
    log_handle = FRONTEND_LOG.open("w", encoding="utf-8")
    print_line("Запускаю frontend...")
    return subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(FRONTEND_PORT)],
        cwd=FRONTEND_DIR,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )


def ensure_runtime_dir() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def wait_forever() -> int:
    while True:
        if BACKEND_PROCESS is not None and BACKEND_PROCESS.poll() is not None:
            print_line("Backend завершился. Смотри лог-файл.")
            print_log_tail(BACKEND_LOG, "Backend log tail")
            return BACKEND_PROCESS.returncode or 1

        if FRONTEND_PROCESS is not None and FRONTEND_PROCESS.poll() is not None:
            print_line("Frontend завершился. Смотри лог-файл.")
            print_log_tail(FRONTEND_LOG, "Frontend log tail")
            return FRONTEND_PROCESS.returncode or 1

        time.sleep(1)


def main() -> int:
    global BACKEND_PROCESS, FRONTEND_PROCESS
    args = parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        ensure_runtime_dir()
        if not args.skip_doctor:
            run_doctor(setup_only=args.setup_only)
        if not args.skip_setup:
            run_setup()
        if args.setup_only:
            print_line("Подготовка окружения завершена.")
            return 0

        free_port_or_fail(BACKEND_PORT)
        free_port_or_fail(FRONTEND_PORT)

        BACKEND_PROCESS = start_backend()
        wait_for_http(
            BACKEND_URL,
            BACKEND_PROCESS,
            "Backend",
            BACKEND_LOG,
            args.timeout,
        )

        FRONTEND_PROCESS = start_frontend()
        wait_for_port(
            FRONTEND_PORT,
            FRONTEND_PROCESS,
            "Frontend",
            FRONTEND_LOG,
            args.timeout,
        )

        print()
        print_line("Приложение запущено:")
        print(f"  Frontend: http://localhost:{FRONTEND_PORT}")
        print(f"  Backend : http://localhost:{BACKEND_PORT}")
        print("  Логин   : engineer")
        print("  Пароль  : engineer123")
        print(f"  Логи    : {RUNTIME_DIR}")
        print()
        print_line("Для остановки нажми Ctrl+C")

        return wait_forever()
    except subprocess.CalledProcessError as error:
        print_line(
            f"Ошибка: команда завершилась с кодом {error.returncode}: {' '.join(error.cmd)}"
        )
        return error.returncode or 1
    except RuntimeError as error:
        print_line(f"Ошибка: {error}")
        return 1
    finally:
        cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
