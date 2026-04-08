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


ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
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


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
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
    max_lines: int = 8,
) -> str:
    output_lines: list[str] = []
    for raw_line in (result.stderr + "\n" + result.stdout).splitlines():
        line = raw_line.strip()
        if line:
            output_lines.append(line)

    if not output_lines:
        output_lines = [fallback_message]

    preview = output_lines[:max_lines]
    if len(output_lines) > max_lines:
        preview.append("... (обрезано)")

    joined_preview = "\n".join(preview)
    return f"Команда: {shell_join(command)}\n{joined_preview}"


def detect_backend_python() -> str:
    venv_python = BACKEND_DIR / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def check_backend_compile(python_bin: str) -> CheckResult:
    command = [python_bin, "-m", "compileall", "app"]
    result = run_command(command, cwd=BACKEND_DIR)
    if result.returncode == 0:
        return CheckResult(
            "backend: проверка синтаксиса (compileall)", CheckStatus.PASS
        )

    return CheckResult(
        "backend: проверка синтаксиса (compileall)",
        CheckStatus.FAIL,
        build_error_details(command, result, "Не удалось выполнить compileall"),
    )


def check_backend_pytest(python_bin: str) -> CheckResult:
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
        build_error_details(command, result, "Тесты не прошли"),
    )


def check_backend_lint(python_bin: str) -> CheckResult:
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
        build_error_details(command, result, "ruff нашёл ошибки"),
    )


def check_backend_format(python_bin: str) -> CheckResult:
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
        build_error_details(command, result, "black обнаружил неотформатированный код"),
    )


def check_backend_pep8(python_bin: str) -> CheckResult:
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
        build_error_details(command, result, "pycodestyle нашёл нарушения PEP8"),
    )


def check_frontend_build() -> CheckResult:
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
        build_error_details(command, result, "Сборка frontend завершилась ошибкой"),
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
    started = perf_counter()
    result = fn()
    result.name = name
    result.duration_sec = perf_counter() - started
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NetOps Assistant doctor: автоматические проверки проекта"
    )
    parser.add_argument(
        "--scope",
        choices=["all", "backend", "frontend"],
        default="all",
        help="какие проверки запускать (по умолчанию: all)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="быстрый режим: пропустить долгие проверки (например frontend сборку)",
    )
    parser.add_argument(
        "--autofix",
        action="store_true",
        help="Перед проверками автоматически исправить то, что безопасно чинится (`ruff --fix`, `black`).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    python_bin = detect_backend_python()
    results: list[CheckResult] = []
    started_total = perf_counter()

    if args.autofix and args.scope in {"all", "backend"}:
        autofix_messages = try_backend_autofix(python_bin)
        for message in autofix_messages:
            print(f"[АВТОФИКС] {message}")

    if args.scope in {"all", "backend"}:
        results.append(
            timed_check(
                "backend: проверка синтаксиса (compileall)",
                lambda: check_backend_compile(python_bin),
            )
        )
        results.append(
            timed_check(
                "backend: линтер (ruff)", lambda: check_backend_lint(python_bin)
            )
        )
        results.append(
            timed_check(
                "backend: форматирование (black --check)",
                lambda: check_backend_format(python_bin),
            )
        )
        results.append(
            timed_check(
                "backend: PEP8 (pycodestyle)",
                lambda: check_backend_pep8(python_bin),
            )
        )
        results.append(
            timed_check(
                "backend: автотесты (pytest)", lambda: check_backend_pytest(python_bin)
            )
        )

    if args.scope in {"all", "frontend"}:
        results.append(
            timed_check("frontend: локализация интерфейса", check_frontend_localization)
        )
        results.append(
            timed_check(
                "frontend: понятные внутренние имена",
                check_frontend_internal_names,
            )
        )
        results.append(
            timed_check(
                "frontend: поясняющие комментарии в сложных файлах",
                check_frontend_explanatory_comments,
            )
        )
        if args.quick:
            results.append(
                timed_check(
                    "frontend: сборка",
                    lambda: CheckResult(
                        "frontend: сборка",
                        CheckStatus.SKIP,
                        "пропущено из-за --quick",
                    ),
                )
            )
        else:
            results.append(timed_check("frontend: сборка", check_frontend_build))

    for result in results:
        print_result(result)
    total_duration_sec = perf_counter() - started_total
    print_summary(results, total_duration_sec)

    has_failures = any(r.status == CheckStatus.FAIL for r in results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
