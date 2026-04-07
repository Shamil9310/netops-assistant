import { Sidebar } from "@/components/sidebar";
import { getHealth } from "@/lib/api";
import { requireUser } from "@/lib/auth";

const widgets = [
  { title: "CPU", value: "14%", note: "целевая телеметрия VM" },
  { title: "RAM", value: "41%", note: "использование памяти" },
  { title: "Disk", value: "28%", note: "свободное место и рост архивов" },
  { title: "Exports", value: "ok", note: "pipeline выгрузок" },
];

export default async function DeveloperPage() {
  const user = await requireUser();
  const health = await getHealth();

  if (user.role !== "developer") {
    return (
      <div className="shell">
        <Sidebar user={user} />
        <main className="content-col" style={{ padding: 24 }}>
          <div className="report-block">
            <div className="report-header-title">Доступ запрещён</div>
            <div className="report-header-sub">Раздел доступен только роли developer.</div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Developer</div>
        <div className="focus-note">
          <div className="focus-note-label">Важно</div>
          <p>В production этот раздел должен быть доступен только developer role.</p>
        </div>
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Developer Dashboard</div>
            <div className="page-sub">Системные метрики VM и техническое состояние платформы</div>
          </div>
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
          <pre className="export">backend: {health?.status ?? "offline"}
database: planned
ldap adapter: planned
export pipeline: planned
observability: planned</pre>
        </div>
      </main>
    </div>
  );
}
