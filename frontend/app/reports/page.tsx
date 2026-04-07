import { Sidebar } from "@/components/sidebar";
import { requireUser } from "@/lib/auth";

const dailyReport = `Отчёт о проделанной работе
Дата: 7 апреля 2026 · Инженер: Шамиль Исаев

── ЗАДАЧИ ──────────────────────────────────────
  10:00–10:30  (30 мин)
  Обновление NetBox — обсуждение плана миграции.

── ИНЦИДЕНТЫ ───────────────────────────────────
  11:10–12:20  (70 мин)
  SR11683266 — Разбор инцидента BGP-маршрутизации.

── ИЗМЕНЕНИЯ ───────────────────────────────────
  13:00–14:40  (100 мин)
  WA00468580 — Подготовка плана ночных работ.

── ОБСЛУЖИВАНИЕ ────────────────────────────────
  15:00–16:00  (60 мин)
  Актуализация тестового стенда NetBox.

── ИТОГО ───────────────────────────────────────
  Записей: 4  ·  Время: 4ч 20мин`;

export default async function ReportsPage() {
  const user = await requireUser();

  return (
    <div className="shell">
      <Sidebar user={user} />

      {/* Filter col */}
      <aside className="filter-col">
        <div className="filter-col-title">Параметры</div>

        <div style={{ marginBottom: 16 }}>
          <div className="filter-date-label">Тип отчёта</div>
          <div className="tab-bar" style={{ display: "flex", width: "100%" }}>
            <button className="tab active" style={{ flex: 1 }}>День</button>
            <button className="tab" style={{ flex: 1 }}>Неделя</button>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div className="filter-date-label">Дата</div>
          <input type="date" className="filter-date-input" defaultValue="2026-04-07" />
        </div>

        <div className="filter-divider" />

        <div className="filter-group">
          <div className="filter-group-title">Статистика недели</div>
          <div className="filter-stat-row">
            <span className="filter-stat-label" style={{ color: "var(--red)" }}>Инцидентов</span>
            <span className="filter-stat-val" style={{ color: "var(--red)" }}>8</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label" style={{ color: "var(--blue)" }}>Задач</span>
            <span className="filter-stat-val" style={{ color: "var(--blue)" }}>14</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label" style={{ color: "var(--green)" }}>Изменений</span>
            <span className="filter-stat-val" style={{ color: "var(--green)" }}>5</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Обслуживание</span>
            <span className="filter-stat-val">3</span>
          </div>
        </div>

        <div className="focus-note">
          <div className="focus-note-label">Подсказка</div>
          <p>Выбери период и нажми «Сформировать» — отчёт соберётся из журнала.</p>
        </div>
      </aside>

      {/* Content */}
      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Отчёты</div>
            <div className="page-sub">Дневные и недельные сводки из журнала</div>
          </div>
          <div className="toolbar">
            <button className="btn btn-primary">Сформировать</button>
          </div>
        </div>

        <div className="section-label">Дневной отчёт · 7 апреля 2026</div>

        <div className="report-block">
          <div className="report-header">
            <div>
              <div className="report-header-title">7 апреля 2026</div>
              <div className="report-header-sub">Автосборка · 4 записи · Шамиль Исаев</div>
            </div>
          </div>
          <pre className="export">{dailyReport}</pre>
          <div className="export-bar">
            <span className="export-label">Скачать:</span>
            <button className="export-btn">📄 TXT</button>
            <button className="export-btn">📝 MD</button>
            <button className="export-btn">📘 DOCX</button>
            <button className="export-btn">📕 PDF</button>
          </div>
        </div>
      </main>
    </div>
  );
}
