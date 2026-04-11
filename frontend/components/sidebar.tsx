"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { CurrentUser } from "@/lib/api";
import { LogoutButton } from "@/components/logout-button";

function getSections(role: string) {
  const baseSections = [
    {
      title: "Разделы",
      items: [
        { href: "/dashboard", icon: "◈", label: "Дашборд" },
        { href: "/journal", icon: "☰", label: "Журнал" },
        { href: "/reports", icon: "⬡", label: "Отчёты" },
        { href: "/kanban", icon: "◫", label: "Канбан" },
        { href: "/templates", icon: "◎", label: "Шаблоны" },
        { href: "/archive", icon: "▣", label: "Архив" },
      ],
    },
    {
      title: "Команда",
      items: [{ href: "/team", icon: "◉", label: "Состав" }],
    },
  ];

  if (role === "developer") {
    baseSections.push({
      title: "Сервис",
      items: [
        { href: "/developer", icon: "◌", label: "Разработчик" },
        { href: "/developer/users", icon: "◎", label: "Учётки" },
      ],
    });
  }
  return baseSections;
}

export function Sidebar({ user }: { user: CurrentUser }) {
  const pathname = usePathname();
  const sections = getSections(user.role);
  const initials = user.full_name
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("");
  const isActivePath = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
    <aside className="nav-col">
      <div className="brand">
        <div className="brand-mark">NA</div>
        <div>
          <div className="brand-title">Ассистент NetOps</div>
          <div className="brand-subtitle">Рабочее пространство для сетевых операций</div>
        </div>
      </div>

      <div className="sidebar-status">
        <div className="sidebar-status-label">Рабочая зона</div>
        <div className="sidebar-status-value">{user.role}</div>
        <div className="sidebar-status-note">Безопасная сессия активна</div>
      </div>

      <nav className="nav">
        {sections.map((section) => (
          <div key={section.title}>
            <div className="nav-section">{section.title}</div>
            {section.items.map(({ href, icon, label }) => (
              <Link key={href} href={href} className={isActivePath(href) ? "active" : ""}>
                <span className="nav-icon">{icon}</span>
                {label}
              </Link>
            ))}
          </div>
        ))}
      </nav>

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
