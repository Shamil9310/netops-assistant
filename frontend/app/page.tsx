import { Sidebar } from "@/components/sidebar";
import { getHealth } from "@/lib/api";
import { requireUser } from "@/lib/auth";

const timeline = [
  { time: "10:00", dur: "30 мин", cat: "task",        title: "Обновление NetBox — план миграции",       desc: "Обсуждение плана миграции и рисков отката." },
  { time: "11:10", dur: "70 мин", cat: "incident",     title: "SR11683266 — Разбор инцидента BGP",       desc: "Проверка BGP-соседства и маршрутов в рабочем контуре." },
  { time: "13:00", dur: "100 мин", cat: "change",      title: "WA00468580 — Подготовка плана работ",    desc: "Pre-check, rollback и post-check команды." },
  { time: "15:00", dur: "60 мин",  cat: "maintenance", title: "Актуализация тестового стенда NetBox",    desc: "Версия, LDAP и сценарий миграции." },
];

const catLabel: Record<string, string> = {
  incident:    "Инцидент",
  task:        "Задача",
  change:      "Изменение",
  maintenance: "Обслуживание",
};

const reportDraft = `Отчёт за 7 апреля 2026
Инженер: Шамиль Исаев

── ЗАДАЧИ ──────────────────────────────────
  10:00–10:30  (30 мин)
  Обновление NetBox — план миграции.

── ИНЦИДЕНТЫ ───────────────────────────────
  11:10–12:20  (70 мин)
  SR11683266 — Разбор инцидента BGP.

── ИЗМЕНЕНИЯ ───────────────────────────────
  13:00–14:40  (100 мин)
  WA00468580 — Подготовка плана ночных работ.

── ОБСЛУЖИВАНИЕ ────────────────────────────
  15:00–16:00  (60 мин)
  Актуализация стенда NetBox.

── ИТОГО ───────────────────────────────────
  Записей: 4  ·  Время: 4ч 20мин`;

export default async function HomePage() {
  const user = await requireUser();
  const health = await getHealth();

  return (
    <div className="shell">
      <Sidebar user={user} />

      {/* Filter col */}
      <aside className="filter-col">
        <div className="filter-col-title">Сегодня</div>

        <div style={{ marginBottom: 20 }}>
          <div className="filter-date-label">Дата</div>
          <input type="date" className="filter-date-input" defaultValue="2026-04-07" />
        </div>

        <div className="filter-group">
          <div className="filter-group-title">Статистика</div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Созвоны</span>
            <span className="filter-stat-val" style={{ color: "var(--green)" }}>2ч 20м</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Заявки</span>
            <span className="filter-stat-val" style={{ color: "var(--blue)" }}>7</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Заполненность</span>
            <span className="filter-stat-val" style={{ color: "var(--amber)" }}>82%</span>
          </div>
          <div className="filter-stat-row" style={{ marginTop: 6 }}>
            <span className="filter-stat-label">Backend</span>
            <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, fontWeight: 600 }}>
              <span className="status-dot" />
              {health?.status ?? "offline"}
            </span>
          </div>
        </div>

        <div className="focus-note">
          <div className="focus-note-label">Фокус дня</div>
          <p>Завершить WA00468580, проверить rollback, собрать дневной отчёт.</p>
        </div>
      </aside>

      {/* Content */}
      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Рабочий день</div>
            <div className="page-sub">Понедельник, 7 апреля 2026</div>
          </div>
          <div className="toolbar">
            <button className="btn btn-primary">+ Запись</button>
            <button className="btn">Отчёт</button>
          </div>
        </div>

        {/* Timeline */}
        <div className="section-label">Лента дня</div>
        <div className="day-group">
          <div className="entry-list">
            {timeline.map((e) => (
              <div key={e.title} className="entry-item">
                <div className={`entry-accent-bar ${e.cat}`} />
                <div className="entry-body">
                  <div className="entry-head">
                    <span className={`badge ${e.cat}`}>
                      <span className={`badge-dot ${e.cat}`} />
                      {catLabel[e.cat]}
                    </span>
                    <span className="entry-title">{e.title}</span>
                    <span className="entry-time">{e.time} · {e.dur}</span>
                  </div>
                  <div className="entry-desc">{e.desc}</div>
                </div>
                <div className="entry-actions">
                  <button className="btn btn-sm btn-ghost">✎</button>
                  <button className="btn btn-sm btn-danger">✕</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Report draft */}
        <div className="section-label">Черновик отчёта</div>
        <div className="report-block">
          <div className="report-header">
            <div>
              <div className="report-header-title">7 апреля 2026</div>
              <div className="report-header-sub">Автосборка · 4 записи</div>
            </div>
          </div>
          <pre className="export">{reportDraft}</pre>
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
