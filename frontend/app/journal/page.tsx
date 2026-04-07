import { Sidebar } from "@/components/sidebar";
import { requireUser } from "@/lib/auth";

const entries = [
  { time: "09:30", dur: "60 мин",  cat: "task",        title: "Проверка приоритетных SR",               desc: "Разобрать новые задачи и определить порядок работы." },
  { time: "10:00", dur: "30 мин",  cat: "task",        title: "TrueConf — созвон по NetBox",            desc: "Фиксация решений по миграции." },
  { time: "11:10", dur: "70 мин",  cat: "incident",    title: "SR11683266 — Разбор инцидента BGP",      desc: "Проверка сессии, маршрутов и соседей." },
  { time: "13:00", dur: "100 мин", cat: "change",      title: "WA00468580 — Подготовка плана работ",   desc: "Pre-check, config, rollback, пост-проверки." },
];

const prevEntries = [
  { time: "09:30", dur: "90 мин",  cat: "task",     title: "Аудит конфигурации BGP RST-DC3",            desc: "Проверка peer-группы и route-map политик." },
  { time: "14:15", dur: "45 мин",  cat: "incident", title: "SR11679841 — Потеря связи с MPLS-сегментом", desc: "Диагностика и восстановление MPLS-тоннеля." },
];

const catLabel: Record<string, string> = {
  incident: "Инцидент", task: "Задача", change: "Изменение", maintenance: "Обслуживание",
};

export default async function JournalPage() {
  const user = await requireUser();

  return (
    <div className="shell">
      <Sidebar user={user} />

      {/* Filter col */}
      <aside className="filter-col">
        <div className="filter-col-title">Фильтры</div>

        <div style={{ marginBottom: 20 }}>
          <div className="filter-date-label">Дата</div>
          <input type="date" className="filter-date-input" defaultValue="2026-04-07" />
        </div>

        <div className="filter-group">
          <div className="filter-group-title">Категория</div>
          <button className="filter-chip active">
            <span className="chip-dot" style={{ background: "var(--text-2)" }} /> Все записи
            <span className="chip-count">6</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--red)" }} /> Инциденты
            <span className="chip-count">2</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--blue)" }} /> Задачи
            <span className="chip-count">3</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--green)" }} /> Изменения
            <span className="chip-count">1</span>
          </button>
          <button className="filter-chip">
            <span className="chip-dot" style={{ background: "var(--text-3)" }} /> Обслуживание
            <span className="chip-count">0</span>
          </button>
        </div>

        <div className="filter-divider" />

        <div className="filter-group">
          <div className="filter-group-title">Статистика дня</div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Записей</span>
            <span className="filter-stat-val">4</span>
          </div>
          <div className="filter-stat-row">
            <span className="filter-stat-label">Время</span>
            <span className="filter-stat-val" style={{ color: "var(--green)" }}>4ч 20м</span>
          </div>
        </div>

        <div className="focus-note">
          <div className="focus-note-label">Фокус дня</div>
          <p>Завершить WA00468580 и собрать дневной отчёт.</p>
        </div>
      </aside>

      {/* Content */}
      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Журнал</div>
            <div className="page-sub">История записей по дням</div>
          </div>
          <div className="toolbar">
            <input className="search-input" placeholder="🔍  Поиск..." />
            <button className="btn btn-primary">+ Запись</button>
          </div>
        </div>

        {/* Today */}
        <div className="day-group">
          <div className="day-label">
            Сегодня, 7 апреля
            <span className="day-label-count">4 записи</span>
          </div>
          <div className="entry-list">
            {entries.map((e) => (
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

        {/* Yesterday */}
        <div className="day-group">
          <div className="day-label">
            Вчера, 6 апреля
            <span className="day-label-count">2 записи</span>
          </div>
          <div className="entry-list">
            {prevEntries.map((e) => (
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
      </main>
    </div>
  );
}
