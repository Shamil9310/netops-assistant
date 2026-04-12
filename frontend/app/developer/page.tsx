import { Sidebar } from "@/components/sidebar";
import { getHealth } from "@/lib/api";
import { requireUser } from "@/lib/auth";

const widgets = [
  { title: "CPU", value: "14%", note: "целевая телеметрия VM" },
  { title: "RAM", value: "41%", note: "использование памяти" },
  { title: "Диск", value: "28%", note: "свободное место и рост архивов" },
  { title: "Выгрузки", value: "ok", note: "конвейер выгрузок" },
];

export default async function DeveloperPage() {
  const user = await requireUser();
  const health = await getHealth();

  if (user.role !== "developer") {
    return (
      <div className="shell shell-developer">
        <Sidebar user={user} />
        <main className="content-col" style={{ padding: 24 }}>
          <div className="report-block">
            <div className="report-header-title">Доступ запрещён</div>
            <div className="report-header-sub">Раздел доступен только роли разработчика.</div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="shell shell-developer">
      <Sidebar user={user} />

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Панель разработчика</div>
            <div className="page-sub">Системные метрики VM и техническое состояние платформы</div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 16,
          }}
        >
          {widgets.map((widget) => (
            <div key={widget.title} className="report-block" style={{ padding: 18 }}>
              <div className="badge task">{widget.title}</div>
              <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
                {widget.value}
              </div>
              <div className="page-sub">{widget.note}</div>
            </div>
          ))}
        </div>

        <div className="section-label">Ключевые метрики</div>
        <div className="plan-list" style={{ marginBottom: 24 }}>
          {widgets.map((widget) => (
            <div key={widget.title} className="plan-item">
              <div className="plan-icon ospf">◌</div>
              <div className="plan-info">
                <div className="plan-title">{widget.title}: {widget.value}</div>
                <div className="plan-sub">{widget.note}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="section-label">Сервисы</div>
        <div className="report-block">
          <pre className="export">backend: {health?.status ?? "недоступен"}
база данных: запланировано
LDAP-адаптер: запланировано
конвейер выгрузки: запланировано
наблюдаемость: запланировано</pre>
        </div>
      </main>

      <aside className="filter-col developer-filter-col">
        <div className="filter-col-title">Разработчик</div>
        <div className="focus-note">
          <div className="focus-note-label">Разделы</div>
          <p>Управление учётными записями вынесено на отдельную страницу в сервисном меню.</p>
        </div>
      </aside>
    </div>
  );
}
