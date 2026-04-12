"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type NavItem = {
  href: string;
  icon: string;
  label: string;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

type SidebarNavProps = {
  sections: NavSection[];
};

export function SidebarNav({ sections }: SidebarNavProps) {
  const pathname = usePathname();
  const isActivePath = (href: string) =>
    pathname === href || pathname.startsWith(`${href}/`);

  return (
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
  );
}
