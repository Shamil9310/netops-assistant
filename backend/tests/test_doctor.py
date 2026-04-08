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
