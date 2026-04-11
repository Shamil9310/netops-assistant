from __future__ import annotations

import importlib.util
from types import SimpleNamespace
from pathlib import Path

import pytest


def load_run_local_module():
    """Загружает локальный раннер как обычный Python-модуль для unit-тестов."""
    project_root_dir = Path(__file__).resolve().parents[2]
    script_path = project_root_dir / "scripts" / "run_local_app.py"
    module_spec = importlib.util.spec_from_file_location(
        "run_local_app_test_module", script_path
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("Не удалось загрузить scripts/run_local_app.py")

    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_resolve_project_venv_python_returns_existing_binary(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Локальный раннер должен использовать именно Python из корневого venv проекта."""
    run_local_module = load_run_local_module()
    fake_python_path = tmp_path / ".venv" / "bin" / "python"
    fake_python_path.parent.mkdir(parents=True)
    fake_python_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(run_local_module, "ROOT_DIR", tmp_path)

    resolved_path = run_local_module.resolve_project_venv_python()

    assert resolved_path == str(fake_python_path)


def test_resolve_project_venv_python_raises_clear_error_when_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Если venv ещё не создан, сообщение должно подсказывать следующий шаг."""
    run_local_module = load_run_local_module()
    monkeypatch.setattr(run_local_module, "ROOT_DIR", tmp_path)

    with pytest.raises(RuntimeError, match="Сначала выполни подготовку окружения"):
        run_local_module.resolve_project_venv_python()


def test_ensure_backend_dependencies_installs_dev_extras(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Локальная подготовка должна ставить и runtime, и dev-зависимости backend."""
    run_local_module = load_run_local_module()
    captured_calls: list[tuple[list[str], Path]] = []

    def fake_run_command(command: list[str], cwd: Path, check: bool = True, env=None):
        del check, env
        captured_calls.append((command, cwd))
        return None

    monkeypatch.setattr(run_local_module, "run_command", fake_run_command)

    run_local_module.ensure_backend_dependencies("/tmp/project/.venv/bin/python")

    assert captured_calls == [
        (
            [
                "/tmp/project/.venv/bin/python",
                "-m",
                "pip",
                "install",
                "-e",
                ".[dev]",
            ],
            run_local_module.BACKEND_DIR,
        )
    ]


def test_bootstrap_scripts_keep_dev_extras_installation() -> None:
    """Shell- и Python-скрипты подготовки не должны откатываться к runtime-only установке."""
    project_root_dir = Path(__file__).resolve().parents[2]
    run_local_script = (project_root_dir / "scripts" / "run_local_app.py").read_text(
        encoding="utf-8"
    )
    deploy_vm_script = (project_root_dir / "scripts" / "deploy_vm.sh").read_text(
        encoding="utf-8"
    )

    assert 'pip", "install", "-e", ".[dev]"' in run_local_script
    assert 'pip install -e ".[dev]"' in deploy_vm_script
    assert "pip install -e ." not in deploy_vm_script


def test_run_doctor_uses_bootstrap_missing_and_logs_runtime_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_local должен явно показывать команду doctor и используемое окружение."""
    run_local_module = load_run_local_module()
    printed_messages: list[str] = []
    captured_subprocess_call: dict[str, object] = {}

    def fake_print_line(message: str) -> None:
        printed_messages.append(message)

    def fake_subprocess_run(command, cwd, check=False):
        del check
        captured_subprocess_call["command"] = command
        captured_subprocess_call["cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(run_local_module, "print_line", fake_print_line)
    monkeypatch.setattr(run_local_module.subprocess, "run", fake_subprocess_run)

    run_local_module.run_doctor(setup_only=False)

    assert captured_subprocess_call["command"] == [
        run_local_module.sys.executable,
        str(run_local_module.ROOT_DIR / "doctor.py"),
        "--ci",
        "all",
        "--autofix",
        "--bootstrap-missing",
    ]
    assert captured_subprocess_call["cwd"] == run_local_module.ROOT_DIR
    assert any("Корень проекта:" in message for message in printed_messages)
    assert any("Python запуска run_local:" in message for message in printed_messages)
    assert any("Ожидаемый Python проекта:" in message for message in printed_messages)
    assert any("Команда doctor:" in message for message in printed_messages)


def test_main_runs_setup_before_doctor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """На чистом проекте сначала готовим окружение, потом запускаем doctor."""
    run_local_module = load_run_local_module()
    call_order: list[str] = []

    monkeypatch.setattr(
        run_local_module,
        "parse_args",
        lambda: SimpleNamespace(
            timeout=60,
            skip_setup=False,
            setup_only=True,
            skip_doctor=False,
        ),
    )
    monkeypatch.setattr(run_local_module, "ensure_runtime_dir", lambda: None)
    monkeypatch.setattr(run_local_module, "print_line", lambda _message: None)
    monkeypatch.setattr(
        run_local_module.signal, "signal", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(run_local_module, "cleanup", lambda: None)
    monkeypatch.setattr(
        run_local_module, "run_setup", lambda: call_order.append("run_setup")
    )
    monkeypatch.setattr(
        run_local_module,
        "run_doctor",
        lambda setup_only=False: call_order.append(f"run_doctor:{setup_only}"),
    )

    result = run_local_module.main()

    assert result == 0
    assert call_order == ["run_setup", "run_doctor:True"]
