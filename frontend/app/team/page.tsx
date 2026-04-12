import { Sidebar } from "@/components/sidebar";
import { PageHero } from "@/components/page-hero";
import { getMyTeamMembers, getTeamWeeklySummary } from "@/lib/api";
import { requireUser } from "@/lib/auth";

function getCurrentWeekMondayIso(): string {
  const now = new Date();
  const day = now.getDay(); // Sunday = 0, Monday = 1
  const diffToMonday = day === 0 ? -6 : 1 - day;
  const monday = new Date(now);
  monday.setDate(now.getDate() + diffToMonday);
  monday.setHours(0, 0, 0, 0);
  return monday.toISOString().slice(0, 10);
}

export default async function TeamPage() {
  const user = await requireUser();
  const weekStart = getCurrentWeekMondayIso();
  const members = await getMyTeamMembers();
  const weeklySummary = await getTeamWeeklySummary(weekStart);
  const publicApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  function getRoleLabel(role: string): string {
    const labels: Record<string, string> = {
      developer: "разработчик",
      manager: "начальник",
      employee: "пользователь",
    };
    return labels[role] ?? role;
  }

  return (
    <div className="shell">
      <Sidebar user={user} />

      <main className="content-col">
        <PageHero
          eyebrow="Командный контур"
          title="Команда"
          subtitle="Сотрудники моего контура и их роли."
          stats={[
            { label: "Участники", value: String((members ?? []).length), hint: "В моём контуре" },
            { label: "Неделя", value: weekStart, hint: "Старт отчётного периода" },
            { label: "Отчёты", value: String(weeklySummary?.reduce((sum, item) => sum + item.total_entries, 0) ?? 0), hint: "Записей за неделю" },
            { label: "Статус", value: "view", hint: "Без редактирования" },
          ]}
        />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Участники</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {(members ?? []).length}
            </div>
            <div className="page-sub">В моём контуре</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge bgp">Неделя</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {weekStart}
            </div>
            <div className="page-sub">Старт отчётного периода</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge acl">Отчёты</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {weeklySummary?.reduce((sum, item) => sum + item.total_entries, 0) ?? 0}
            </div>
            <div className="page-sub">Записей за неделю</div>
          </div>
        </div>

        <div className="section-label">Участники</div>
        <div className="plan-list">
          {(members ?? []).length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Сотрудники не найдены</div>
                <div className="plan-sub">Возможно, у текущего пользователя нет доступа к контуру начальника.</div>
              </div>
            </div>
          )}

          {(members ?? []).map((member) => (
            <div key={member.id} className="plan-item">
              <div className="plan-icon acl">◉</div>
              <div className="plan-info">
                <div className="plan-title">{member.full_name}</div>
                <div className="plan-sub">
                  {member.username} · роль: {getRoleLabel(member.role)} · статус: {member.is_active ? "активен" : "отключён"}
                </div>
                {member.teams.length > 0 && (
                  <div className="plan-sub">Команды: {member.teams.join(", ")}</div>
                )}
                {weeklySummary && (
                  <div className="plan-sub">
                    Записей за неделю:{" "}
                    {weeklySummary.find((item) => item.user_id === member.id)?.total_entries ?? 0}
                  </div>
                )}
              </div>
              <div className="plan-actions">
                <a className="btn btn-sm" href="/reports">Отчёты</a>
                <a
                  className="btn btn-sm"
                  href={`${publicApiBaseUrl}/api/v1/team/users/${member.id}/reports/weekly/export/md?week_start=${weekStart}`}
                >
                  Недельный MD
                </a>
              </div>
            </div>
          ))}
        </div>

        <div className="section-label">Недельная сводка по команде</div>
        <div className="plan-list">
          {(weeklySummary ?? []).map((item) => (
            <div key={item.user_id} className="plan-item">
              <div className="plan-icon status">Σ</div>
              <div className="plan-info">
                <div className="plan-title">{item.full_name}</div>
                <div className="plan-sub">{item.username} · записей: {item.total_entries}</div>
                <div className="plan-sub">Статусы: {Object.keys(item.by_status).length === 0 ? "нет данных" : Object.entries(item.by_status).map(([status, count]) => `${status}: ${count}`).join(", ")}</div>
                <div className="plan-sub">Типы: {Object.keys(item.by_activity_type).length === 0 ? "нет данных" : Object.entries(item.by_activity_type).map(([activityType, count]) => `${activityType}: ${count}`).join(", ")}</div>
              </div>
            </div>
          ))}
          {(weeklySummary ?? []).length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Сводка пуста</div>
                <div className="plan-sub">За выбранную неделю нет данных по команде.</div>
              </div>
            </div>
          )}
        </div>
      </main>

      <aside className="filter-col">
        <div className="filter-col-title">Командный контур</div>
        <div className="focus-note">
          <div className="focus-note-label">Только просмотр</div>
          <p>Страница показывает сотрудников команды для роли начальника без редактирования чужих данных.</p>
        </div>

        <div className="filter-divider" />

        <div className="focus-note">
          <div className="focus-note-label">Недельная сводка</div>
          <p>Текущая неделя: {weekStart}. Сводка собирается по дневному журналу всей команды.</p>
        </div>
      </aside>
    </div>
  );
}
