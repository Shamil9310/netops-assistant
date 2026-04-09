#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from time import perf_counter
from typing import Callable


class CheckStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(slots=True)
class CheckResult:
    name: str
    status: CheckStatus
    details: str = ""
    duration_sec: float = 0.0


@dataclass(slots=True)
class DoctorCommand:
    checks: list[str]
    quick: bool = False
    autofix: bool = False
    full: bool = False
    show_help: bool = False
    should_exit: bool = False
    ci: bool = False


@dataclass(slots=True)
class DependencyInstallPlan:
    key: str
    title: str
    description: str


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
DEFAULT_BACKEND_COVERAGE_THRESHOLD = 50
FRONTEND_UI_DIRS = (FRONTEND_DIR / "app", FRONTEND_DIR / "components")
FRONTEND_CODE_DIRS = (
    FRONTEND_DIR / "app",
    FRONTEND_DIR / "components",
    FRONTEND_DIR / "lib",
)
FRONTEND_COMMENT_REQUIRED_DIRS = (
    FRONTEND_DIR / "app" / "api",
    FRONTEND_DIR / "components",
)
FRONTEND_UI_EXTENSIONS = {".ts", ".tsx"}
ALLOWED_UI_ENGLISH_WORDS = {
    "API",
    "BGP",
    "BPM",
    "CPU",
    "DOCX",
    "email",
    "JSON",
    "PDF",
    "RAM",
    "SR",
    "TXT",
    "UI",
    "VM",
    "MD",
    "LDAP",
    "RU",
    "EN",
    "NetOps",
    "Assistant",
    "NetOps Assistant",
}
STRING_LITERAL_RE = re.compile(r'"([^"\n]+)"|\'([^\'\n]+)\'')
TEXT_NODE_RE = re.compile(r">([^<{]+)<")
ENGLISH_WORD_RE = re.compile(r"[A-Za-z][A-Za-z-]*")
GENERIC_FRONTEND_NAME_RE = re.compile(
    r"\b(?:const|let)\s+(body|data|result|payload|value)\b"
)
GENERIC_FRONTEND_LOOP_NAME_RE = re.compile(
    r"\bfor\s*\(\s*(?:const|let)\s+(value)\s+of\b"
)
COMMENT_LINE_RE = re.compile(r"^\s*(//|/\*|\*|\{/\*)")
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
COMPLEXITY_PATTERNS = (
    re.compile(r"\bif\s*\("),
    re.compile(r"\btry\b"),
    re.compile(r"\bcatch\b"),
    re.compile(r"\bfor\s*\("),
    re.compile(r"\bwhile\s*\("),
    re.compile(r"\.map\s*\("),
    re.compile(r"\.filter\s*\("),
    re.compile(r"\.flatMap\s*\("),
)
COMMENT_REQUIRED_MIN_LINES = 150
COMMENT_REQUIRED_MIN_COMPLEXITY = 10
COMMENT_REQUIRED_MIN_COMMENTS = 2
CHECK_CHOICES = (
    "all",
    "compileall",
    "ruff",
    "black",
    "pep8",
    "mypy",
    "pytest",
    "coverage",
    "localization",
    "names",
    "comments",
    "build",
)
CHECKS_BY_SCOPE = {
    "backend": ["compileall", "ruff", "black", "pep8", "mypy", "pytest", "coverage"],
    "frontend": ["localization", "names", "comments", "build"],
    "all": [
        "compileall",
        "ruff",
        "black",
        "pep8",
        "mypy",
        "pytest",
        "coverage",
        "localization",
        "names",
        "comments",
        "build",
    ],
}
BACKEND_AUTOFIX_TRIGGER_CHECKS = {
    "compileall",
    "ruff",
    "black",
    "pep8",
    "mypy",
    "pytest",
}
LAST_CHECK_RESULTS: list[CheckResult] = []


def print_action(message: str) -> None:
    print(f"[doctor] {message}", flush=True)


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    relative_cwd = cwd.relative_to(ROOT_DIR) if cwd != ROOT_DIR else Path(".")
    print_action(f"Запуск команды в {relative_cwd}: {shell_join(command)}")
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )


def shell_join(parts: list[str]) -> str:
    return " ".join(parts)


def build_error_details(
    command: list[str],
    result: subprocess.CompletedProcess[str],
    fallback_message: str,
    max_lines: int | None = 8,
) -> str:
    output_lines: list[str] = []
    for raw_line in (result.stderr + "\n" + result.stdout).splitlines():
        line = raw_line.strip()
        if line:
            output_lines.append(line)

    if not output_lines:
        output_lines = [fallback_message]

    if max_lines is None:
        preview = output_lines
    else:
        preview = output_lines[:max_lines]
        if len(output_lines) > max_lines:
            preview.append("... (обрезано)")

    joined_preview = "\n".join(preview)
    return f"Команда: {shell_join(command)}\n{joined_preview}"


def detect_backend_python() -> str:
    candidate_pythons = (
        BACKEND_DIR / ".venv" / "bin" / "python",
        ROOT_DIR / ".venv" / "bin" / "python",
    )
    for candidate_python in candidate_pythons:
        if candidate_python.exists():
            return str(candidate_python)
    return sys.executable


def check_backend_compile(python_bin: str, full: bool = False) -> CheckResult:
    command = [python_bin, "-m", "compileall", "app"]
    result = run_command(command, cwd=BACKEND_DIR)
    if result.returncode == 0:
        return CheckResult(
            "backend: проверка синтаксиса (compileall)", CheckStatus.PASS
        )

    return CheckResult(
        "backend: проверка синтаксиса (compileall)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "Не удалось выполнить compileall",
            max_lines=None if full else 8,
        ),
    )


def check_backend_coverage(python_bin: str, full: bool = False) -> CheckResult:
    has_pytest_cov = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('pytest_cov') is not None)",
        ],
        cwd=BACKEND_DIR,
    )
    if has_pytest_cov.returncode != 0 or "True" not in has_pytest_cov.stdout:
        return CheckResult(
            "backend: покрытие тестами (coverage)",
            CheckStatus.SKIP,
            "pytest-cov не установлен (активируй backend/.venv и установи dev-зависимости)",
        )

    command = [
        python_bin,
        "-m",
        "pytest",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=xml:coverage.xml",
        f"--cov-fail-under={DEFAULT_BACKEND_COVERAGE_THRESHOLD}",
        "-q",
    ]
    result = run_command(command, cwd=BACKEND_DIR)
    if result.returncode == 0:
        coverage_line = next(
            (line for line in result.stdout.splitlines() if "TOTAL" in line), ""
        )
        details_parts: list[str] = []
        if coverage_line:
            details_parts.append(coverage_line.strip())
        details_parts.append(f"XML-отчёт сохранён в {Path('backend') / 'coverage.xml'}")
        return CheckResult(
            "backend: покрытие тестами (coverage)",
            CheckStatus.PASS,
            "\n".join(details_parts),
        )

    return CheckResult(
        "backend: покрытие тестами (coverage)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "Покрытие ниже порога или тесты упали",
            max_lines=None if full else 12,
        ),
    )


def check_backend_pytest(python_bin: str, full: bool = False) -> CheckResult:
    has_pytest = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('pytest') is not None)",
        ],
        cwd=BACKEND_DIR,
    )
    if has_pytest.returncode != 0 or "True" not in has_pytest.stdout:
        return CheckResult(
            "backend: автотесты (pytest)",
            CheckStatus.SKIP,
            "pytest не установлен (активируй backend/.venv и установи dev-зависимости)",
        )

    command = [python_bin, "-m", "pytest", "-q"]
    result = run_command(command, cwd=BACKEND_DIR)
    if result.returncode == 0:
        return CheckResult("backend: автотесты (pytest)", CheckStatus.PASS)

    return CheckResult(
        "backend: автотесты (pytest)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "Тесты не прошли",
            max_lines=None if full else 8,
        ),
    )


def check_backend_lint(python_bin: str, full: bool = False) -> CheckResult:
    has_ruff = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('ruff') is not None)",
        ],
        cwd=ROOT_DIR,
    )
    if has_ruff.returncode != 0 or "True" not in has_ruff.stdout:
        return CheckResult(
            "backend: линтер (ruff)", CheckStatus.SKIP, "ruff не установлен"
        )

    command = [
        python_bin,
        "-m",
        "ruff",
        "check",
        "backend/app",
        "backend/tests",
        "doctor.py",
    ]
    result = run_command(command, cwd=ROOT_DIR)
    if result.returncode == 0:
        return CheckResult("backend: линтер (ruff)", CheckStatus.PASS)
    return CheckResult(
        "backend: линтер (ruff)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "ruff нашёл ошибки",
            max_lines=None if full else 8,
        ),
    )


def check_backend_format(python_bin: str, full: bool = False) -> CheckResult:
    has_black = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('black') is not None)",
        ],
        cwd=ROOT_DIR,
    )
    if has_black.returncode != 0 or "True" not in has_black.stdout:
        return CheckResult(
            "backend: форматирование (black --check)",
            CheckStatus.SKIP,
            "black не установлен",
        )

    command = [
        python_bin,
        "-m",
        "black",
        "--check",
        "backend/app",
        "backend/tests",
        "doctor.py",
    ]
    result = run_command(command, cwd=ROOT_DIR)
    if result.returncode == 0:
        return CheckResult("backend: форматирование (black --check)", CheckStatus.PASS)
    return CheckResult(
        "backend: форматирование (black --check)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "black обнаружил неотформатированный код",
            max_lines=None if full else 8,
        ),
    )


def check_backend_pep8(python_bin: str, full: bool = False) -> CheckResult:
    has_pycodestyle = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('pycodestyle') is not None)",
        ],
        cwd=ROOT_DIR,
    )
    if has_pycodestyle.returncode != 0 or "True" not in has_pycodestyle.stdout:
        return CheckResult(
            "backend: PEP8 (pycodestyle)",
            CheckStatus.SKIP,
            "pycodestyle не установлен",
        )

    command = [
        python_bin,
        "-m",
        "pycodestyle",
        "--max-line-length=140",
        "backend/app",
        "backend/tests",
        "doctor.py",
    ]
    result = run_command(command, cwd=ROOT_DIR)
    if result.returncode == 0:
        return CheckResult("backend: PEP8 (pycodestyle)", CheckStatus.PASS)
    return CheckResult(
        "backend: PEP8 (pycodestyle)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "pycodestyle нашёл нарушения PEP8",
            max_lines=None if full else 8,
        ),
    )


def check_backend_mypy(python_bin: str, full: bool = False) -> CheckResult:
    has_mypy = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('mypy') is not None)",
        ],
        cwd=ROOT_DIR,
    )
    if has_mypy.returncode != 0 or "True" not in has_mypy.stdout:
        return CheckResult(
            "backend: типизация (mypy)",
            CheckStatus.SKIP,
            "mypy не установлен",
        )

    command = [python_bin, "-m", "mypy", "app"]
    result = run_command(command, cwd=BACKEND_DIR)
    if result.returncode == 0:
        return CheckResult("backend: типизация (mypy)", CheckStatus.PASS)

    return CheckResult(
        "backend: типизация (mypy)",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "mypy нашёл ошибки",
            max_lines=None if full else 8,
        ),
    )


def check_frontend_build(full: bool = False) -> CheckResult:
    if shutil.which("npm") is None:
        return CheckResult("frontend: сборка", CheckStatus.SKIP, "npm не найден")

    if not (FRONTEND_DIR / "node_modules").exists():
        return CheckResult(
            "frontend: сборка",
            CheckStatus.SKIP,
            "нет frontend/node_modules (выполни npm install)",
        )

    command = ["npm", "run", "-s", "build"]
    result = run_command(command, cwd=FRONTEND_DIR)
    if result.returncode == 0:
        return CheckResult("frontend: сборка", CheckStatus.PASS)

    return CheckResult(
        "frontend: сборка",
        CheckStatus.FAIL,
        build_error_details(
            command,
            result,
            "Сборка frontend завершилась ошибкой",
            max_lines=None if full else 8,
        ),
    )


def iter_frontend_ui_files(root_dir: Path = ROOT_DIR) -> list[Path]:
    files: list[Path] = []
    for source_dir in FRONTEND_UI_DIRS:
        resolved_dir = (
            root_dir / source_dir.relative_to(ROOT_DIR)
            if root_dir != ROOT_DIR
            else source_dir
        )
        if not resolved_dir.exists():
            continue
        for path in sorted(resolved_dir.rglob("*")):
            if "api" in path.parts:
                continue
            if path.is_file() and path.suffix in FRONTEND_UI_EXTENSIONS:
                files.append(path)
    return files


def iter_frontend_code_files(
    source_dirs: tuple[Path, ...], root_dir: Path = ROOT_DIR
) -> list[Path]:
    files: list[Path] = []
    for source_dir in source_dirs:
        resolved_dir = source_dir if source_dir.is_absolute() else root_dir / source_dir
        if not resolved_dir.exists():
            continue
        for path in sorted(resolved_dir.rglob("*")):
            if path.is_file() and path.suffix in FRONTEND_UI_EXTENSIONS:
                files.append(path)
    return files


def normalize_candidate(raw_value: str) -> str:
    return " ".join(raw_value.replace("\\n", " ").split())


def should_ignore_candidate(candidate: str) -> bool:
    if not candidate:
        return True
    if len(candidate) < 3:
        return True
    if candidate in ALLOWED_UI_ENGLISH_WORDS:
        return True
    if "(" in candidate or ")" in candidate:
        return True
    if re.fullmatch(r"[A-Z]{2,}", candidate):
        return True
    if re.fullmatch(r"[a-z]{2}-[A-Z]{2}", candidate):
        return True
    if "{{" in candidate or "}}" in candidate:
        return True
    if re.fullmatch(r"[A-Za-z0-9._-]+", candidate):
        return True
    if len(candidate) > 20 and re.fullmatch(r"[A-Za-z]+", candidate):
        return True
    if "var(--" in candidate:
        return True
    if "/" in candidate or "@" in candidate or "http" in candidate:
        return True
    if candidate.startswith("use client"):
        return True
    if re.fullmatch(r"[a-z0-9_:-]+", candidate):
        return True
    if re.fullmatch(r"[a-z0-9_-]+(?: [a-z0-9_-]+)*", candidate):
        return True
    if (
        re.fullmatch(r"[A-Z0-9_-]+", candidate)
        and candidate in ALLOWED_UI_ENGLISH_WORDS
    ):
        return True
    return False


def find_suspicious_ui_strings(source_text: str) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []

    for line_number, raw_line in enumerate(source_text.splitlines(), start=1):
        candidates: list[str] = []
        candidates.extend(
            normalize_candidate(match.group(1) or match.group(2) or "")
            for match in STRING_LITERAL_RE.finditer(raw_line)
        )
        candidates.extend(
            normalize_candidate(match.group(1))
            for match in TEXT_NODE_RE.finditer(raw_line)
        )

        seen_for_line: set[str] = set()
        for candidate in candidates:
            if candidate in seen_for_line or should_ignore_candidate(candidate):
                continue
            seen_for_line.add(candidate)

            english_words = ENGLISH_WORD_RE.findall(candidate)
            if not english_words:
                continue

            unknown_words = [
                word
                for word in english_words
                if word.rstrip("-") not in ALLOWED_UI_ENGLISH_WORDS
                and word.rstrip("-").upper() not in ALLOWED_UI_ENGLISH_WORDS
            ]
            if not unknown_words:
                continue

            findings.append((line_number, candidate))

    return findings


def find_generic_frontend_names(source_text: str) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    for line_number, raw_line in enumerate(source_text.splitlines(), start=1):
        for pattern in (GENERIC_FRONTEND_NAME_RE, GENERIC_FRONTEND_LOOP_NAME_RE):
            match = pattern.search(raw_line)
            if match is not None:
                findings.append((line_number, match.group(1)))
    return findings


def check_frontend_internal_names() -> CheckResult:
    findings: list[str] = []
    for file_path in iter_frontend_code_files(FRONTEND_CODE_DIRS):
        relative_path = file_path.relative_to(ROOT_DIR)
        file_findings = find_generic_frontend_names(
            file_path.read_text(encoding="utf-8")
        )
        for line_number, variable_name in file_findings[:3]:
            findings.append(f"{relative_path}:{line_number}: {variable_name}")
        if len(findings) >= 8:
            break

    if not findings:
        return CheckResult("frontend: понятные внутренние имена", CheckStatus.PASS)

    details = [
        "Найдены слишком общие внутренние имена. Используй более точные названия переменных:"
    ] + findings[:8]
    if len(findings) > 8:
        details.append("... (обрезано)")
    return CheckResult(
        "frontend: понятные внутренние имена",
        CheckStatus.FAIL,
        "\n".join(details),
    )


def count_russian_comment_lines(source_text: str) -> int:
    total = 0
    for raw_line in source_text.splitlines():
        if COMMENT_LINE_RE.search(raw_line) and CYRILLIC_RE.search(raw_line):
            total += 1
    return total


def count_complexity_markers(source_text: str) -> int:
    return sum(len(pattern.findall(source_text)) for pattern in COMPLEXITY_PATTERNS)


def is_comment_required_for_file(source_text: str) -> bool:
    return (
        len(source_text.splitlines()) >= COMMENT_REQUIRED_MIN_LINES
        and count_complexity_markers(source_text) >= COMMENT_REQUIRED_MIN_COMPLEXITY
    )


def check_frontend_explanatory_comments() -> CheckResult:
    findings: list[str] = []
    for file_path in iter_frontend_code_files(FRONTEND_COMMENT_REQUIRED_DIRS):
        source_text = file_path.read_text(encoding="utf-8")
        if not is_comment_required_for_file(source_text):
            continue
        russian_comment_count = count_russian_comment_lines(source_text)
        if russian_comment_count >= COMMENT_REQUIRED_MIN_COMMENTS:
            continue

        relative_path = file_path.relative_to(ROOT_DIR)
        findings.append(
            f"{relative_path}: найдено только {russian_comment_count} поясняющих комментариев"
        )
        if len(findings) >= 8:
            break

    if not findings:
        return CheckResult(
            "frontend: поясняющие комментарии в сложных файлах",
            CheckStatus.PASS,
        )

    details = [
        "В сложных frontend-файлах не хватает русских поясняющих комментариев:"
    ] + findings
    return CheckResult(
        "frontend: поясняющие комментарии в сложных файлах",
        CheckStatus.FAIL,
        "\n".join(details),
    )


def check_frontend_localization() -> CheckResult:
    findings: list[str] = []
    for file_path in iter_frontend_ui_files(ROOT_DIR):
        relative_path = file_path.relative_to(ROOT_DIR)
        file_findings = find_suspicious_ui_strings(
            file_path.read_text(encoding="utf-8")
        )
        for line_number, candidate in file_findings[:5]:
            findings.append(f"{relative_path}:{line_number}: {candidate}")
        if len(findings) >= 8:
            break

    if not findings:
        return CheckResult("frontend: локализация интерфейса", CheckStatus.PASS)

    details = ["Найдены подозрительные английские строки в русской UI:"] + findings[:8]
    if len(findings) > 8:
        details.append("... (обрезано)")
    return CheckResult(
        "frontend: локализация интерфейса",
        CheckStatus.FAIL,
        "\n".join(details),
    )


def try_backend_autofix(python_bin: str) -> list[str]:
    messages: list[str] = []

    has_ruff = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('ruff') is not None)",
        ],
        cwd=ROOT_DIR,
    )
    if has_ruff.returncode == 0 and "True" in has_ruff.stdout:
        ruff_fix = run_command(
            [
                python_bin,
                "-m",
                "ruff",
                "check",
                "--fix",
                "backend/app",
                "backend/tests",
                "doctor.py",
            ],
            cwd=ROOT_DIR,
        )
        if ruff_fix.returncode == 0:
            messages.append("Автоисправление `ruff --fix` выполнено")

    has_black = run_command(
        [
            python_bin,
            "-c",
            "import importlib.util; print(importlib.util.find_spec('black') is not None)",
        ],
        cwd=ROOT_DIR,
    )
    if has_black.returncode == 0 and "True" in has_black.stdout:
        black_fix = run_command(
            [
                python_bin,
                "-m",
                "black",
                "backend/app",
                "backend/tests",
                "doctor.py",
            ],
            cwd=ROOT_DIR,
        )
        if black_fix.returncode == 0:
            messages.append("Автоформатирование `black` выполнено")

    return messages


def collect_installable_dependency_plans(
    results: list[CheckResult],
) -> list[DependencyInstallPlan]:
    plans: list[DependencyInstallPlan] = []
    seen_keys: set[str] = set()

    for result in results:
        if result.status != CheckStatus.SKIP:
            continue

        if result.name.startswith("backend:") and (
            "не установлен" in result.details
            or "активируй backend/.venv" in result.details
            or "dev-зависимости" in result.details
        ):
            if "backend-dev" not in seen_keys:
                plans.append(
                    DependencyInstallPlan(
                        key="backend-dev",
                        title="backend: виртуальное окружение и dev-зависимости",
                        description="Создать `backend/.venv`, обновить `pip` и установить `pip install -e .[dev]`.",
                    )
                )
                seen_keys.add("backend-dev")
            continue

        if (
            result.name == "frontend: сборка"
            and "frontend/node_modules" in result.details
        ):
            if "frontend-node-modules" not in seen_keys:
                plans.append(
                    DependencyInstallPlan(
                        key="frontend-node-modules",
                        title="frontend: зависимости npm",
                        description="Выполнить `npm install` в каталоге `frontend`.",
                    )
                )
                seen_keys.add("frontend-node-modules")

    return plans


def ensure_backend_venv() -> tuple[bool, str]:
    backend_venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    if backend_venv_python.exists():
        return True, ""

    bootstrap_python = shutil.which("python3") or sys.executable
    command = [bootstrap_python, "-m", "venv", str(BACKEND_DIR / ".venv")]
    result = run_command(command, cwd=ROOT_DIR)
    if result.returncode == 0:
        return True, ""

    return False, build_error_details(
        command,
        result,
        "Не удалось создать backend/.venv",
        max_lines=12,
    )


def install_backend_dev_dependencies() -> tuple[bool, str]:
    created, details = ensure_backend_venv()
    if not created:
        return False, details

    backend_python = str(BACKEND_DIR / ".venv" / "bin" / "python")
    commands = [
        [backend_python, "-m", "pip", "install", "--upgrade", "pip"],
        [backend_python, "-m", "pip", "install", "-e", ".[dev]"],
    ]

    for command in commands:
        result = run_command(command, cwd=BACKEND_DIR)
        if result.returncode != 0:
            return False, build_error_details(
                command,
                result,
                "Не удалось установить backend-зависимости",
                max_lines=12,
            )

    return True, ""


def install_frontend_node_modules() -> tuple[bool, str]:
    if shutil.which("npm") is None:
        return (
            False,
            "npm не найден. Автоматически установить frontend-зависимости нельзя.",
        )

    command = ["npm", "install"]
    result = run_command(command, cwd=FRONTEND_DIR)
    if result.returncode == 0:
        return True, ""

    return False, build_error_details(
        command,
        result,
        "Не удалось установить frontend-зависимости",
        max_lines=12,
    )


def install_dependency_plans(plans: list[DependencyInstallPlan]) -> bool:
    for plan in plans:
        print_action(f"Устанавливаю зависимости: {plan.title}")
        match plan.key:
            case "backend-dev":
                ok, details = install_backend_dev_dependencies()
            case "frontend-node-modules":
                ok, details = install_frontend_node_modules()
            case _:
                ok = False
                details = f"Неизвестный план установки: {plan.key}"

        if not ok:
            print(f"[ОШИБКА] Не удалось завершить установку: {plan.title}")
            if details:
                for line in details.splitlines():
                    print(f"  {line}")
            return False

    return True


def prompt_yes_no(prompt_text: str) -> bool:
    answer = input(prompt_text).strip().lower()
    return answer in {"y", "yes", "д", "да"}


def prompt_install_missing_dependencies(results: list[CheckResult]) -> bool:
    install_plans = collect_installable_dependency_plans(results)
    if not install_plans:
        return False

    print("")
    print_action(
        "Некоторые проверки пропущены из-за отсутствующих зависимостей. Можно установить их сейчас."
    )
    for index, plan in enumerate(install_plans, start=1):
        print(f"  {index}. {plan.title}")
        print(f"     {plan.description}")

    if not prompt_yes_no("Установить сейчас? [y/N]: "):
        print_action("Установку зависимостей пропускаю по выбору пользователя.")
        return False

    return install_dependency_plans(install_plans)


def print_result(result: CheckResult) -> None:
    status_label = {
        CheckStatus.PASS: "ОК",
        CheckStatus.FAIL: "ОШИБКА",
        CheckStatus.SKIP: "ПРОПУЩЕНО",
    }[result.status]
    print(f"[{status_label}] {result.name} ({result.duration_sec:.2f}s)")
    if result.details:
        for line in result.details.splitlines():
            print(f"  {line}")


def print_summary(results: list[CheckResult], total_duration_sec: float) -> None:
    total = len(results)
    passed = sum(1 for r in results if r.status == CheckStatus.PASS)
    failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIP)
    print("")
    print("Сводка doctor")
    print(f"  Всего проверок: {total}")
    print(f"  ОК:             {passed}")
    print(f"  Ошибки:         {failed}")
    print(f"  Пропущено:      {skipped}")
    print(f"  Общее время:    {total_duration_sec:.2f}s")


def timed_check(name: str, fn: Callable[[], CheckResult]) -> CheckResult:
    print_action(f"Начинаю проверку: {name}")
    started = perf_counter()
    result = fn()
    result.name = name
    result.duration_sec = perf_counter() - started
    return result


def parse_check_tokens(raw_checks: list[str] | None) -> list[str]:
    if not raw_checks:
        return []

    checks: list[str] = []
    for raw_value in raw_checks:
        for chunk in raw_value.split(","):
            normalized = chunk.strip().lower()
            if not normalized:
                continue
            if normalized not in CHECK_CHOICES:
                available = ", ".join(CHECK_CHOICES)
                raise argparse.ArgumentTypeError(
                    f"Неизвестная проверка: {normalized}. Доступные проверки: {available}"
                )
            checks.append(normalized)

    unique_checks = list(dict.fromkeys(checks))
    if "all" in unique_checks:
        return CHECKS_BY_SCOPE["all"]
    return unique_checks


def print_available_checks() -> None:
    print("NetOps Assistant doctor")
    print("")
    print("Доступные проверки:")
    for check_name in CHECKS_BY_SCOPE["all"]:
        print(f"  - {check_name}")
    print("")
    print("Как запускать:")
    print("  doctor all")
    print("  doctor --scope backend")
    print("  doctor --scope frontend --quick")
    print("  doctor mypy")
    print("  doctor mypy,pytest")
    print("  doctor coverage")
    print("  doctor mypy autofix")
    print("  doctor all quick")
    print("  doctor mypy full")
    print("")
    print("Модификаторы:")
    print("  quick     пропустить долгие проверки, например build")
    print(
        "  autofix   применить доступные безопасные исправления для выбранных проверок"
    )
    print("  full      показать полный текст ошибок без обрезки")
    print("")
    print("Команды:")
    print("  help      показать список ещё раз")
    print("  exit      завершить doctor")


def parse_command_tokens(raw_tokens: list[str]) -> DoctorCommand:
    normalized_tokens: list[str] = []
    for raw_token in raw_tokens:
        for chunk in raw_token.split(","):
            normalized = chunk.strip().lower().lstrip("-")
            if normalized:
                normalized_tokens.append(normalized)

    if not normalized_tokens:
        return DoctorCommand(checks=[])

    if len(normalized_tokens) == 1 and normalized_tokens[0] in {"help", "h", "?"}:
        return DoctorCommand(checks=[], show_help=True)

    if len(normalized_tokens) == 1 and normalized_tokens[0] in {"exit", "quit", "q"}:
        return DoctorCommand(checks=[], should_exit=True)

    quick = False
    autofix = False
    full = False
    checks: list[str] = []

    for token in normalized_tokens:
        if token in {"help", "h", "?"}:
            return DoctorCommand(checks=[], show_help=True)
        if token in {"exit", "quit", "q"}:
            return DoctorCommand(checks=[], should_exit=True)
        if token == "quick":
            quick = True
            continue
        if token in {"autofix", "fix"}:
            autofix = True
            continue
        if token == "full":
            full = True
            continue
        checks.append(token)

    return DoctorCommand(
        checks=parse_check_tokens(checks),
        quick=quick,
        autofix=autofix,
        full=full,
    )


def prompt_for_command(prompt_text: str = "doctor> ") -> DoctorCommand:
    while True:
        print("")
        user_value = input(prompt_text).strip()
        if not user_value:
            print_action("Пустая команда. Введи help, exit, all или нужные проверки.")
            continue
        try:
            command = parse_command_tokens(user_value.split())
        except argparse.ArgumentTypeError as exc:
            print_action(str(exc))
            continue
        if command.show_help:
            print_available_checks()
            continue
        return command


def parse_args() -> DoctorCommand:
    raw_argv = sys.argv[1:]

    ci_mode = "--ci" in raw_argv or not sys.stdin.isatty() or not sys.stdout.isatty()
    filtered_argv = [a for a in raw_argv if a != "--ci"]

    scope_value: str | None = None
    compatibility_tokens: list[str] = []
    index = 0
    while index < len(filtered_argv):
        token = filtered_argv[index]
        if token == "--scope":
            if index + 1 >= len(filtered_argv):
                raise SystemExit(
                    "Флаг --scope требует значение: backend, frontend или all"
                )
            scope_value = filtered_argv[index + 1].strip().lower()
            index += 2
            continue
        if token.startswith("--scope="):
            scope_value = token.split("=", 1)[1].strip().lower()
            index += 1
            continue
        if token == "--quick":
            compatibility_tokens.append("quick")
            index += 1
            continue
        if token == "--autofix":
            compatibility_tokens.append("autofix")
            index += 1
            continue
        if token == "--full":
            compatibility_tokens.append("full")
            index += 1
            continue
        compatibility_tokens.append(token)
        index += 1

    expanded_scope_checks: list[str] = []
    if scope_value is not None:
        if scope_value not in CHECKS_BY_SCOPE:
            available_scopes = ", ".join(CHECKS_BY_SCOPE)
            raise SystemExit(
                f"Неизвестный scope: {scope_value}. Доступные scope: {available_scopes}"
            )
        expanded_scope_checks = CHECKS_BY_SCOPE[scope_value]

    if not compatibility_tokens:
        if ci_mode:
            print_action(
                "CI-режим: проверки не указаны. Передай имена проверок аргументами."
            )
            raise SystemExit(1)
        print_available_checks()
        return prompt_for_command()

    if len(compatibility_tokens) == 1 and compatibility_tokens[0].strip().lower() in {
        "help",
        "--help",
        "-h",
    }:
        print_available_checks()
        raise SystemExit(0)

    command = parse_command_tokens(compatibility_tokens)
    if expanded_scope_checks:
        command.checks = list(dict.fromkeys([*expanded_scope_checks, *command.checks]))
    if ci_mode:
        command.ci = True
    return command


def resolve_requested_checks(command: DoctorCommand) -> list[str]:
    return command.checks


def run_autofix_for_checks(requested_checks: list[str], python_bin: str) -> list[str]:
    messages: list[str] = []

    if any(check in BACKEND_AUTOFIX_TRIGGER_CHECKS for check in requested_checks):
        backend_messages = try_backend_autofix(python_bin)
        if backend_messages:
            messages.extend(backend_messages)
        else:
            messages.append(
                "Для выбранных backend-проверок не найдено доступных автоисправлений"
            )

    unsupported_checks = [
        check
        for check in requested_checks
        if check not in BACKEND_AUTOFIX_TRIGGER_CHECKS
    ]
    if unsupported_checks:
        joined_checks = ", ".join(unsupported_checks)
        messages.append(
            f"Для проверок {joined_checks} безопасные автоисправления пока не реализованы"
        )

    return messages


def run_named_check(
    check_name: str,
    python_bin: str,
    quick: bool,
    full: bool,
) -> CheckResult:
    match check_name:
        case "compileall":
            return timed_check(
                "backend: проверка синтаксиса (compileall)",
                lambda: check_backend_compile(python_bin, full=full),
            )
        case "ruff":
            return timed_check(
                "backend: линтер (ruff)",
                lambda: check_backend_lint(python_bin, full=full),
            )
        case "black":
            return timed_check(
                "backend: форматирование (black --check)",
                lambda: check_backend_format(python_bin, full=full),
            )
        case "pep8":
            return timed_check(
                "backend: PEP8 (pycodestyle)",
                lambda: check_backend_pep8(python_bin, full=full),
            )
        case "mypy":
            return timed_check(
                "backend: типизация (mypy)",
                lambda: check_backend_mypy(python_bin, full=full),
            )
        case "pytest":
            return timed_check(
                "backend: автотесты (pytest)",
                lambda: check_backend_pytest(python_bin, full=full),
            )
        case "coverage":
            return timed_check(
                "backend: покрытие тестами (coverage)",
                lambda: check_backend_coverage(python_bin, full=full),
            )
        case "localization":
            return timed_check(
                "frontend: локализация интерфейса", check_frontend_localization
            )
        case "names":
            return timed_check(
                "frontend: понятные внутренние имена",
                check_frontend_internal_names,
            )
        case "comments":
            return timed_check(
                "frontend: поясняющие комментарии в сложных файлах",
                check_frontend_explanatory_comments,
            )
        case "build":
            if quick:
                return timed_check(
                    "frontend: сборка",
                    lambda: CheckResult(
                        "frontend: сборка",
                        CheckStatus.SKIP,
                        "пропущено из-за quick",
                    ),
                )
            return timed_check(
                "frontend: сборка",
                lambda: check_frontend_build(full=full),
            )
        case _:
            raise ValueError(f"Неизвестная проверка: {check_name}")


def run_checks(command: DoctorCommand) -> int:
    global LAST_CHECK_RESULTS

    python_bin = detect_backend_python()
    results: list[CheckResult] = []
    started_total = perf_counter()
    requested_checks = resolve_requested_checks(command)

    quick_mode = "yes" if command.quick else "no"
    autofix_mode = "yes" if command.autofix else "no"
    full_mode = "yes" if command.full else "no"
    print_action(
        f"Старт doctor: quick={quick_mode}, "
        f"autofix={autofix_mode}, "
        f"full={full_mode}"
    )
    print_action(f"Выбранные проверки: {', '.join(requested_checks)}")

    if command.autofix:
        autofix_messages = run_autofix_for_checks(requested_checks, python_bin)
        for message in autofix_messages:
            print(f"[АВТОФИКС] {message}")

    for check_name in requested_checks:
        results.append(
            run_named_check(check_name, python_bin, command.quick, command.full)
        )

    for result in results:
        print_result(result)
    total_duration_sec = perf_counter() - started_total
    print_summary(results, total_duration_sec)
    LAST_CHECK_RESULTS = list(results)

    has_failures = any(r.status == CheckStatus.FAIL for r in results)
    return 1 if has_failures else 0


def main() -> int:
    command = parse_args()
    last_exit_code = 0

    if command.ci:
        if not command.checks:
            print_action("CI-режим: проверки не указаны.")
            return 1
        return run_checks(command)

    while True:
        if command.should_exit:
            print_action("Завершаю doctor")
            return last_exit_code

        if not command.checks:
            print_action(
                "Не выбраны проверки. Введи help, exit, all или нужные проверки."
            )
        else:
            last_exit_code = run_checks(command)
            if prompt_install_missing_dependencies(LAST_CHECK_RESULTS):
                print("")
                print_action(
                    "Зависимости установлены. Повторно запускаю те же проверки."
                )
                last_exit_code = run_checks(command)

        print("")
        print_action("Я закончил. Что дальше? Введи следующую проверку, help или exit.")
        command = prompt_for_command()


if __name__ == "__main__":
    raise SystemExit(main())
