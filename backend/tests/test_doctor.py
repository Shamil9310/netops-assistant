from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def import_doctor_module():
    project_root = Path(__file__).resolve().parents[2]
    doctor_path = project_root / "doctor.py"
    spec = importlib.util.spec_from_file_location("netops_doctor", doctor_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_find_suspicious_ui_strings_flags_english_user_facing_text() -> None:
    doctor = import_doctor_module()

    source = """
    <div>Developer Dashboard</div>
    <input placeholder="Ticket number" />
    """

    findings = doctor.find_suspicious_ui_strings(source)

    assert (2, "Developer Dashboard") in findings
    assert (3, "Ticket number") in findings


def test_find_suspicious_ui_strings_allows_vm_sr_and_internal_values() -> None:
    doctor = import_doctor_module()

    source = """
    <div>Системные метрики VM и SR</div>
    if (user.role !== "developer") {
      return null;
    }
    <option value="draft">Черновик</option>
    const endpoint = "/api/v1/reports";
    """

    findings = doctor.find_suspicious_ui_strings(source)

    assert findings == []


def test_find_generic_frontend_names_reports_common_placeholders() -> None:
    doctor = import_doctor_module()

    source = """
    const payload = await request.json();
    const responsePayload = await response.json();
    for (const value of randomValues) {
      console.log(value);
    }
    """

    findings = doctor.find_generic_frontend_names(source)

    assert (2, "payload") in findings
    assert (4, "value") in findings
    assert all(name != "responsePayload" for _, name in findings)


def test_check_frontend_internal_names_reports_file_and_line(
    monkeypatch, tmp_path: Path
) -> None:
    doctor = import_doctor_module()
    frontend_dir = tmp_path / "frontend"
    app_dir = frontend_dir / "app"
    components_dir = frontend_dir / "components"
    lib_dir = frontend_dir / "lib"
    app_dir.mkdir(parents=True)
    components_dir.mkdir(parents=True)
    lib_dir.mkdir(parents=True)

    (app_dir / "page.tsx").write_text(
        "const payload = await request.json();\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(doctor, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(
        doctor, "FRONTEND_CODE_DIRS", (app_dir, components_dir, lib_dir)
    )

    check_result = doctor.check_frontend_internal_names()

    assert check_result.status == doctor.CheckStatus.FAIL
    assert "frontend/app/page.tsx:1: payload" in check_result.details


def test_check_frontend_explanatory_comments_flags_complex_file_without_comments(
    monkeypatch, tmp_path: Path
) -> None:
    doctor = import_doctor_module()
    frontend_dir = tmp_path / "frontend"
    components_dir = frontend_dir / "components"
    components_dir.mkdir(parents=True)

    (components_dir / "complex.tsx").write_text(
        "\n".join(
            [
                "export function ComplexWidget() {",
                "  if (a) return null;",
                "  if (b) return null;",
                "  try {",
                "    items.map((item) => item);",
                "    items.filter(Boolean);",
                "  } catch (error) {",
                "    return null;",
                "  }",
                "  for (const entry of items) {",
                "    console.log(entry);",
                "  }",
                "  return <div />;",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(doctor, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(doctor, "FRONTEND_COMMENT_REQUIRED_DIRS", (components_dir,))
    monkeypatch.setattr(doctor, "COMMENT_REQUIRED_MIN_LINES", 10)
    monkeypatch.setattr(doctor, "COMMENT_REQUIRED_MIN_COMPLEXITY", 6)
    monkeypatch.setattr(doctor, "COMMENT_REQUIRED_MIN_COMMENTS", 1)

    check_result = doctor.check_frontend_explanatory_comments()

    assert check_result.status == doctor.CheckStatus.FAIL
    assert "frontend/components/complex.tsx" in check_result.details


def test_check_frontend_explanatory_comments_passes_with_russian_comments(
    monkeypatch, tmp_path: Path
) -> None:
    doctor = import_doctor_module()
    frontend_dir = tmp_path / "frontend"
    components_dir = frontend_dir / "components"
    components_dir.mkdir(parents=True)

    (components_dir / "complex.tsx").write_text(
        "\n".join(
            [
                "// Обрабатываем ветки отображения формы",
                "export function ComplexWidget() {",
                "  // Ошибки сети не должны ломать экран целиком",
                "  if (a) return null;",
                "  if (b) return null;",
                "  try {",
                "    items.map((item) => item);",
                "    items.filter(Boolean);",
                "  } catch (error) {",
                "    return null;",
                "  }",
                "  for (const entry of items) {",
                "    console.log(entry);",
                "  }",
                "  return <div />;",
                "}",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(doctor, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(doctor, "FRONTEND_COMMENT_REQUIRED_DIRS", (components_dir,))
    monkeypatch.setattr(doctor, "COMMENT_REQUIRED_MIN_LINES", 10)
    monkeypatch.setattr(doctor, "COMMENT_REQUIRED_MIN_COMPLEXITY", 6)
    monkeypatch.setattr(doctor, "COMMENT_REQUIRED_MIN_COMMENTS", 2)

    check_result = doctor.check_frontend_explanatory_comments()

    assert check_result.status == doctor.CheckStatus.PASS


def test_check_frontend_localization_reports_file_and_line(
    monkeypatch, tmp_path: Path
) -> None:
    doctor = import_doctor_module()
    frontend_dir = tmp_path / "frontend"
    app_dir = frontend_dir / "app"
    components_dir = frontend_dir / "components"
    app_dir.mkdir(parents=True)
    components_dir.mkdir(parents=True)

    (app_dir / "page.tsx").write_text(
        '<div className="page-title">Weekly summary</div>\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(doctor, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(doctor, "FRONTEND_DIR", frontend_dir)
    monkeypatch.setattr(
        doctor,
        "FRONTEND_UI_DIRS",
        (frontend_dir / "app", frontend_dir / "components"),
    )

    check_result = doctor.check_frontend_localization()

    assert check_result.status == doctor.CheckStatus.FAIL
    assert "frontend/app/page.tsx:1: Weekly summary" in check_result.details


def test_check_frontend_localization_passes_on_russian_ui(
    monkeypatch, tmp_path: Path
) -> None:
    doctor = import_doctor_module()
    frontend_dir = tmp_path / "frontend"
    app_dir = frontend_dir / "app"
    components_dir = frontend_dir / "components"
    app_dir.mkdir(parents=True)
    components_dir.mkdir(parents=True)

    (app_dir / "page.tsx").write_text(
        '<div className="page-title">Недельная сводка по VM и SR</div>\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(doctor, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(doctor, "FRONTEND_DIR", frontend_dir)
    monkeypatch.setattr(
        doctor,
        "FRONTEND_UI_DIRS",
        (frontend_dir / "app", frontend_dir / "components"),
    )

    check_result = doctor.check_frontend_localization()

    assert check_result.status == doctor.CheckStatus.PASS
    assert check_result.details == ""


def test_parse_check_tokens_supports_single_check() -> None:
    doctor = import_doctor_module()

    parsed = doctor.parse_check_tokens(["mypy"])

    assert parsed == ["mypy"]


def test_parse_check_tokens_supports_comma_separated_values() -> None:
    doctor = import_doctor_module()

    parsed = doctor.parse_check_tokens(["mypy,pytest", "ruff"])

    assert parsed == ["mypy", "pytest", "ruff"]


def test_parse_check_tokens_expands_all_keyword() -> None:
    doctor = import_doctor_module()

    parsed = doctor.parse_check_tokens(["all"])

    assert parsed == doctor.CHECKS_BY_SCOPE["all"]


def test_parse_check_tokens_supports_new_quality_checks() -> None:
    doctor = import_doctor_module()

    parsed = doctor.parse_check_tokens(["eradicate,interrogate,pydocstyle"])

    assert parsed == ["eradicate", "interrogate", "pydocstyle"]


def test_resolve_requested_checks_uses_explicit_check_list() -> None:
    doctor = import_doctor_module()

    class Args:
        checks = ["mypy", "pytest"]

    resolved = doctor.resolve_requested_checks(Args())

    assert resolved == ["mypy", "pytest"]


def test_parse_command_tokens_supports_quick_and_autofix_modifiers() -> None:
    doctor = import_doctor_module()

    command = doctor.parse_command_tokens(["mypy,pytest", "quick", "autofix", "full"])

    assert command.checks == ["mypy", "pytest"]
    assert command.quick is True
    assert command.autofix is True
    assert command.full is True


def test_parse_command_tokens_supports_report_issues_command() -> None:
    doctor = import_doctor_module()

    command = doctor.parse_command_tokens(["report", "issues"])

    assert command.checks == []
    assert command.report_mode == "issues"


def test_build_completion_candidates_suggests_top_level_commands() -> None:
    doctor = import_doctor_module()

    candidates = doctor.build_completion_candidates("")

    assert "all" in candidates
    assert "report" in candidates
    assert "--scope" in candidates


def test_build_completion_candidates_filters_report_modes() -> None:
    doctor = import_doctor_module()

    candidates = doctor.build_completion_candidates("report e")

    assert candidates == ["errors"]


def test_configure_readline_uses_libedit_binding(monkeypatch) -> None:
    doctor = import_doctor_module()

    class FakeReadline:
        __doc__ = "Importing this module enables command line editing using libedit."

        def __init__(self) -> None:
            self.bindings: list[str] = []
            self.completer = None
            self.delims = None

        def set_completer(self, completer) -> None:
            self.completer = completer

        def parse_and_bind(self, binding: str) -> None:
            self.bindings.append(binding)

        def set_completer_delims(self, delims: str) -> None:
            self.delims = delims

    fake_readline = FakeReadline()
    monkeypatch.setattr(doctor, "readline", fake_readline)

    doctor.configure_readline()

    assert fake_readline.completer is doctor.doctor_completer
    assert fake_readline.bindings == ["bind ^I rl_complete"]
    assert fake_readline.delims == " \t\n"


def test_parse_command_tokens_ignores_garbled_prefix_before_all() -> None:
    doctor = import_doctor_module()

    command = doctor.parse_command_tokens(["ф�all"])

    assert command.checks == doctor.CHECKS_BY_SCOPE["all"]


def test_parse_command_tokens_rejects_unknown_report_mode() -> None:
    doctor = import_doctor_module()

    try:
        doctor.parse_command_tokens(["report", "success"])
    except doctor.argparse.ArgumentTypeError as exc:
        assert "issues, errors, skips" in str(exc)
    else:
        raise AssertionError("Ожидали ошибку для неизвестного режима report")


def test_parse_command_tokens_supports_exit_command() -> None:
    doctor = import_doctor_module()

    command = doctor.parse_command_tokens(["exit"])

    assert command.should_exit is True
    assert command.checks == []


def test_run_autofix_for_checks_uses_backend_autofix_for_backend_checks(
    monkeypatch,
) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(
        doctor,
        "try_backend_autofix",
        lambda python_bin: ["Автоисправление backend выполнено"],
    )

    messages = doctor.run_autofix_for_checks(["mypy"], "python")

    assert messages == ["Автоисправление backend выполнено"]


def test_run_autofix_for_checks_reports_missing_autofix_for_frontend_checks() -> None:
    doctor = import_doctor_module()

    messages = doctor.run_autofix_for_checks(["build", "localization"], "python")

    assert (
        "Для проверок build, localization безопасные автоисправления пока не реализованы"
        in messages
    )


def test_parse_args_supports_help_without_dashes(monkeypatch, capsys) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(sys, "argv", ["doctor.py", "help"])

    try:
        doctor.parse_args()
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError(
            "parse_args должен завершаться через SystemExit для doctor help"
        )

    captured = capsys.readouterr()
    assert "NetOps Assistant doctor" in captured.out
    assert "compileall" in captured.out


def test_parse_args_supports_scope_flag(monkeypatch) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(
        sys,
        "argv",
        ["doctor.py", "--scope", "backend", "--quick", "--autofix"],
    )
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)

    args = doctor.parse_args()

    assert args.checks == doctor.CHECKS_BY_SCOPE["backend"]
    assert args.quick is True
    assert args.autofix is True
    assert args.ci is True


def test_detect_backend_python_uses_root_venv(monkeypatch, tmp_path: Path) -> None:
    doctor = import_doctor_module()
    backend_dir = tmp_path / "backend"
    root_venv_python = tmp_path / ".venv" / "bin" / "python"
    backend_dir.mkdir()
    root_venv_python.parent.mkdir(parents=True)
    root_venv_python.write_text("", encoding="utf-8")

    monkeypatch.setattr(doctor, "ROOT_DIR", tmp_path)
    monkeypatch.setattr(doctor, "BACKEND_DIR", backend_dir)

    detected_python = doctor.detect_backend_python()

    assert detected_python == str(root_venv_python)


def test_check_backend_coverage_reports_xml_output(monkeypatch) -> None:
    doctor = import_doctor_module()

    completed_results = iter(
        [
            doctor.subprocess.CompletedProcess(
                args=["python", "-c", "import pytest_cov"],
                returncode=0,
                stdout="True\n",
                stderr="",
            ),
            doctor.subprocess.CompletedProcess(
                args=["python", "-m", "pytest"],
                returncode=0,
                stdout="tests passed\nTOTAL 100 10 90%\n",
                stderr="",
            ),
        ]
    )

    monkeypatch.setattr(
        doctor,
        "run_command",
        lambda command, cwd: next(completed_results),
    )

    check_result = doctor.check_backend_coverage("python")

    assert check_result.status == doctor.CheckStatus.PASS
    assert "TOTAL 100 10 90%" in check_result.details
    assert "backend/coverage.xml" in check_result.details


def test_check_backend_eradicate_passes_when_no_commented_code(monkeypatch) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(
        doctor, "has_python_module", lambda python_bin, module_name, cwd: True
    )
    monkeypatch.setattr(
        doctor,
        "run_command",
        lambda command, cwd: doctor.subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        ),
    )

    check_result = doctor.check_backend_eradicate("python")

    assert check_result.status == doctor.CheckStatus.PASS


def test_check_backend_interrogate_reports_summary_on_success(monkeypatch) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(
        doctor, "has_python_module", lambda python_bin, module_name, cwd: True
    )
    monkeypatch.setattr(
        doctor,
        "run_command",
        lambda command, cwd: doctor.subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="RESULT: PASSED (minimum: 80.0%, actual: 91.0%)\n",
            stderr="",
        ),
    )

    check_result = doctor.check_backend_interrogate("python")

    assert check_result.status == doctor.CheckStatus.PASS
    assert "RESULT: PASSED" in check_result.details


def test_check_backend_pydocstyle_passes_on_clean_docstrings(monkeypatch) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(
        doctor, "has_python_module", lambda python_bin, module_name, cwd: True
    )
    monkeypatch.setattr(
        doctor,
        "run_command",
        lambda command, cwd: doctor.subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="",
            stderr="",
        ),
    )

    check_result = doctor.check_backend_pydocstyle("python")

    assert check_result.status == doctor.CheckStatus.PASS


def test_collect_installable_dependency_plans_finds_backend_and_frontend_items() -> (
    None
):
    doctor = import_doctor_module()

    results = [
        doctor.CheckResult(
            name="backend: автотесты (pytest)",
            status=doctor.CheckStatus.SKIP,
            details="pytest не установлен (активируй .venv и установи dev-зависимости)",
        ),
        doctor.CheckResult(
            name="frontend: сборка",
            status=doctor.CheckStatus.SKIP,
            details="нет frontend/node_modules (выполни npm install)",
        ),
    ]

    plans = doctor.collect_installable_dependency_plans(results)

    assert [plan.key for plan in plans] == ["backend-dev", "frontend-node-modules"]


def test_prompt_install_missing_dependencies_skips_install_on_negative_answer(
    monkeypatch, capsys
) -> None:
    doctor = import_doctor_module()
    results = [
        doctor.CheckResult(
            name="backend: автотесты (pytest)",
            status=doctor.CheckStatus.SKIP,
            details="pytest не установлен (активируй .venv и установи dev-зависимости)",
        )
    ]

    monkeypatch.setattr("builtins.input", lambda _: "n")

    installed = doctor.prompt_install_missing_dependencies(results)

    captured = capsys.readouterr()
    assert installed is False
    assert "Установку зависимостей пропускаю" in captured.out


def test_prompt_install_missing_dependencies_installs_selected_plans(
    monkeypatch,
) -> None:
    doctor = import_doctor_module()
    results = [
        doctor.CheckResult(
            name="backend: покрытие тестами (coverage)",
            status=doctor.CheckStatus.SKIP,
            details="pytest-cov не установлен (активируй .venv и установи dev-зависимости)",
        )
    ]
    installed_plans: list[list[str]] = []

    monkeypatch.setattr("builtins.input", lambda _: "y")
    monkeypatch.setattr(
        doctor,
        "install_dependency_plans",
        lambda plans: installed_plans.append([plan.key for plan in plans]) or True,
    )

    installed = doctor.prompt_install_missing_dependencies(results)

    assert installed is True
    assert installed_plans == [["backend-dev"]]


def test_parse_args_without_arguments_shows_available_checks(
    monkeypatch, capsys
) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(sys, "argv", ["doctor.py"])
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "mypy,pytest")

    args = doctor.parse_args()

    captured = capsys.readouterr()
    assert "Доступные проверки" in captured.out
    assert "doctor all" in captured.out
    assert args.checks == ["mypy", "pytest"]
    assert args.quick is False
    assert args.autofix is False
    assert args.full is False


def test_parse_command_tokens_bootstraps_dependencies_by_default() -> None:
    doctor = import_doctor_module()

    command = doctor.parse_command_tokens(["mypy"])

    assert command.checks == ["mypy"]
    assert command.bootstrap_missing is True


def test_build_error_details_returns_full_output_when_requested() -> None:
    doctor = import_doctor_module()

    result = doctor.subprocess.CompletedProcess(
        args=["python", "-m", "mypy"],
        returncode=1,
        stdout="line3\nline4",
        stderr="line1\nline2",
    )

    details = doctor.build_error_details(
        ["python", "-m", "mypy"],
        result,
        "fallback",
        max_lines=None,
    )

    assert "line1" in details
    assert "line2" in details
    assert "line3" in details
    assert "line4" in details
    assert "... (обрезано)" not in details


def test_print_last_report_shows_only_errors_and_skips(capsys) -> None:
    doctor = import_doctor_module()
    results = [
        doctor.CheckResult(
            name="backend: линтер (ruff)",
            status=doctor.CheckStatus.PASS,
        ),
        doctor.CheckResult(
            name="backend: автотесты (pytest)",
            status=doctor.CheckStatus.FAIL,
            details="Тесты не прошли",
            duration_sec=1.2,
        ),
        doctor.CheckResult(
            name="frontend: сборка",
            status=doctor.CheckStatus.SKIP,
            details="пропущено из-за quick",
            duration_sec=0.0,
        ),
    ]

    doctor.print_last_report(results, "issues")

    captured = capsys.readouterr()
    assert "Отчёт по ошибкам и пропускам" in captured.out
    assert "backend: автотесты (pytest)" in captured.out
    assert "frontend: сборка" in captured.out
    assert "backend: линтер (ruff)" not in captured.out


def test_print_last_report_reports_when_no_errors_or_skips(capsys) -> None:
    doctor = import_doctor_module()
    results = [
        doctor.CheckResult(
            name="backend: линтер (ruff)",
            status=doctor.CheckStatus.PASS,
        )
    ]

    doctor.print_last_report(results, "issues")

    captured = capsys.readouterr()
    assert "В последнем запуске нет ошибок или пропущенных проверок." in captured.out


def test_main_keeps_running_until_exit(monkeypatch) -> None:
    doctor = import_doctor_module()
    executed_checks: list[list[str]] = []

    monkeypatch.setattr(
        doctor,
        "parse_args",
        lambda: doctor.DoctorCommand(checks=["mypy"]),
    )
    monkeypatch.setattr(
        doctor,
        "run_checks",
        lambda command: executed_checks.append(command.checks) or 0,
    )
    monkeypatch.setattr(
        doctor,
        "prompt_for_command",
        lambda prompt_text="doctor> ": doctor.DoctorCommand(
            checks=[], should_exit=True
        ),
    )

    exit_code = doctor.main()

    assert exit_code == 0
    assert executed_checks == [["mypy"]]


def test_main_prints_last_report_without_rerunning_checks(monkeypatch, capsys) -> None:
    doctor = import_doctor_module()
    executed_checks: list[list[str]] = []
    prompted_commands = iter(
        [
            doctor.DoctorCommand(checks=[], report_mode="issues"),
            doctor.DoctorCommand(checks=[], should_exit=True),
        ]
    )

    monkeypatch.setattr(
        doctor,
        "parse_args",
        lambda: doctor.DoctorCommand(checks=["mypy"]),
    )
    monkeypatch.setattr(
        doctor,
        "run_checks",
        lambda command: executed_checks.append(command.checks) or 0,
    )
    monkeypatch.setattr(
        doctor,
        "prompt_for_command",
        lambda prompt_text="doctor> ": next(prompted_commands),
    )
    monkeypatch.setattr(
        doctor,
        "LAST_CHECK_RESULTS",
        [
            doctor.CheckResult(
                name="backend: автотесты (pytest)",
                status=doctor.CheckStatus.FAIL,
                details="Тесты не прошли",
            )
        ],
    )

    exit_code = doctor.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert executed_checks == [["mypy"]]
    assert "Отчёт по ошибкам и пропускам" in captured.out
    assert "backend: автотесты (pytest)" in captured.out


def test_main_prints_command_hints_after_iteration(monkeypatch, capsys) -> None:
    doctor = import_doctor_module()

    monkeypatch.setattr(
        doctor,
        "parse_args",
        lambda: doctor.DoctorCommand(checks=["mypy"]),
    )
    monkeypatch.setattr(
        doctor,
        "run_checks",
        lambda command: 0,
    )
    monkeypatch.setattr(
        doctor,
        "prompt_for_command",
        lambda prompt_text="doctor> ": doctor.DoctorCommand(
            checks=[], should_exit=True
        ),
    )

    exit_code = doctor.main()

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Подсказки по командам:" in captured.out
    assert "report issues | report errors | report skips" in captured.out
