import type { CurrentUser } from "@/lib/api";
import { getSidebarCounters } from "@/lib/api";
import { LogoutButton } from "@/components/logout-button";
import { SidebarNav } from "@/components/sidebar-nav";

function getSections(role: string) {
  const baseSections = [
    {
      title: "Рабочие зоны",
      items: [
        { href: "/dashboard", icon: "◈", label: "Дашборд" },
        { href: "/journal", icon: "☰", label: "Журнал" },
        { href: "/study", icon: "◔", label: "Учёба" },
        { href: "/work-timer", icon: "⏱", label: "Таймер" },
        { href: "/reports", icon: "⬡", label: "Отчёты" },
        { href: "/kanban", icon: "◫", label: "Канбан" },
        { href: "/templates", icon: "◎", label: "Шаблоны" },
        { href: "/archive", icon: "▣", label: "Архив" },
      ],
    },
    {
      title: "Контур",
      items: [{ href: "/team", icon: "◉", label: "Состав" }],
    },
  ];

  if (role === "developer") {
    baseSections.push({
      title: "Служебные",
      items: [
        { href: "/developer", icon: "◌", label: "Разработчик" },
        { href: "/developer/users", icon: "◎", label: "Учётки" },
      ],
    });
  }
  return baseSections;
}

function StatBadge({ label, value }: { label: string; value: number }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 10,
        padding: "8px 10px",
        borderRadius: 14,
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <span className="sidebar-status-note" style={{ margin: 0 }}>
        {label}
      </span>
      <strong style={{ fontSize: 16, color: "var(--text)" }}>{value}</strong>
    </div>
  );
}

export async function Sidebar({ user }: { user: CurrentUser }) {
  const sections = getSections(user.role);
  const stats = await getSidebarCounters();
  const initials = user.full_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("");

  return (
    <aside className="nav-col">
      <div className="brand">
        <div className="brand-mark">NA</div>
        <div>
          <div className="brand-title">Ассистент NetOps</div>
          <div className="brand-subtitle">Единый кабинет для рабочих операций</div>
        </div>
      </div>

      <div className="sidebar-status" style={{ display: "grid", gap: 10 }}>
        <div>
          <div className="sidebar-status-label">Сессия</div>
          <div className="sidebar-status-value">{user.role}</div>
          <div className="sidebar-status-note">Интерфейс готов к работе</div>
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <StatBadge label="Активные планы" value={stats?.activeStudyPlans ?? 0} />
          <StatBadge label="Незакрыто сегодня" value={stats?.unresolvedTasks ?? 0} />
          <StatBadge label="Активные таймеры" value={stats?.activeWorkTimers ?? 0} />
        </div>
      </div>

      <SidebarNav sections={sections} />

      <div className="nav-spacer" />

      <div className="profile-block">
        <div className="profile-row">
          <div className="profile-avatar">{initials}</div>
          <div>
            <div className="profile-name">{user.full_name}</div>
            <div className="profile-role">{user.username}</div>
          </div>
        </div>
        <LogoutButton />
      </div>
    </aside>
  );
}
