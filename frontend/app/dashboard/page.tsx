import { Sidebar } from "@/components/sidebar";
import { DashboardAnalyticsView } from "@/components/dashboard-analytics";
import { getDashboardAnalytics } from "@/lib/api";
import { requireUser } from "@/lib/auth";

export default async function DashboardPage() {
  const user = await requireUser();
  const analytics = await getDashboardAnalytics();

  return (
    <div className="shell shell-two-col">
      <Sidebar user={user} />

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Дашборд</div>
            <div className="page-sub">Исторические графики по заявкам и услугам</div>
          </div>
          <div className="toolbar">
            <a className="btn btn-primary" href="/journal">
              В журнал
            </a>
            <a className="btn" href="/reports">
              Отчёты
            </a>
          </div>
        </div>

        {analytics ? (
          <DashboardAnalyticsView analytics={analytics} />
        ) : (
          <div className="focus-note">
            <div className="focus-note-label">Нет данных</div>
            <p>Сначала добавь записи в журнал, чтобы дашборд начал строить графики.</p>
          </div>
        )}
      </main>
    </div>
  );
}
