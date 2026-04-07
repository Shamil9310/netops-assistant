"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import type { CurrentUser } from "@/lib/api";
import { LogoutButton } from "@/components/logout-button";

const items = [
  { href: "/",        icon: "◈", label: "Сегодня"  },
  { href: "/journal", icon: "☰", label: "Журнал"   },
  { href: "/reports", icon: "⬡", label: "Отчёты"   },
  { href: "/plans",   icon: "◻", label: "Планы"    },
];

export function Sidebar({ user }: { user: CurrentUser }) {
  const pathname = usePathname();
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
        {items.map(({ href, icon, label }) => (
          <Link
            key={href}
            href={href}
            className={pathname === href ? "active" : ""}
          >
            <span className="nav-icon">{icon}</span>
            {label}
          </Link>
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
