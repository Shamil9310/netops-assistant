"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { CurrentUser } from "@/lib/api";
import { LogoutButton } from "@/components/logout-button";

function getSections(role: string) {
  const baseSections = [
    {
      title: "Работа",
      items: [
        { href: "/", icon: "◈", label: "Сегодня" },
        { href: "/journal", icon: "☰", label: "Журнал" },
        { href: "/reports", icon: "⬡", label: "Отчёты" },
        { href: "/plans", icon: "◻", label: "Ночные работы" },
        { href: "/templates", icon: "◎", label: "Шаблоны" },
        { href: "/archive", icon: "▣", label: "Архив" },
      ],
    },
    {
      title: "Команда",
      items: [{ href: "/team", icon: "◉", label: "Команда" }],
    },
  ];

  if (role === "developer") {
    baseSections.push({
      title: "Сервис",
      items: [{ href: "/developer", icon: "◌", label: "Developer" }],
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

  return (
    <aside className="nav-col">
      <div className="brand">
        <div className="brand-mark">NA</div>
        <div>
          <div className="brand-title">NetOps Assistant</div>
          <div className="brand-subtitle">Engineer Workspace</div>
        </div>
      </div>

      <nav className="nav">
        {sections.map((section) => (
          <div key={section.title}>
            <div className="nav-section">{section.title}</div>
            {section.items.map(({ href, icon, label }) => (
              <Link key={href} href={href} className={pathname === href ? "active" : ""}>
                <span className="nav-icon">{icon}</span>
                {label}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="nav-spacer" />

      <div className="lang-switcher">
        <button className="lang-btn active">RU</button>
        <button className="lang-btn">EN</button>
      </div>

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
