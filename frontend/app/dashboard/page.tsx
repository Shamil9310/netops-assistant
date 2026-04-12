import { Sidebar } from "@/components/sidebar";
import { DashboardAnalyticsView } from "@/components/dashboard-analytics";
import { PageHero } from "@/components/page-hero";
import { getDashboardAnalytics } from "@/lib/api";
import { requireUser } from "@/lib/auth";

export default async function DashboardPage() {
  const user = await requireUser();
  const analytics = await getDashboardAnalytics();

  return (
    <div className="shell shell-two-col">
      <Sidebar user={user} />

      <main className="content-col">
        <PageHero
          eyebrow="Командный центр"
          title="Дашборд"
          subtitle="Исторические графики по заявкам, динамике и услугам."
          actions={
            <>
              <a className="btn btn-primary" href="/journal">
                В журнал
              </a>
              <a className="btn" href="/reports">
                Отчёты
              </a>
            </>
          }
          stats={[
            { label: "Всего заявок", value: String(analytics?.total_entries ?? 0), hint: "За период" },
            { label: "Сегодня", value: String(analytics?.today_total ?? 0), hint: "Текущий день" },
            { label: "Неделя", value: String(analytics?.week_total ?? 0), hint: "С начала недели" },
          ]}
        />

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
