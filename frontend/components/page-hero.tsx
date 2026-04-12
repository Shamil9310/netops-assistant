import type { ReactNode } from "react";

type HeroStat = {
  label: string;
  value: string;
  hint?: string;
};

type PageHeroProps = {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  stats?: HeroStat[];
};

export function PageHero({ eyebrow, title, subtitle, actions, stats }: PageHeroProps) {
  return (
    <section className="page-hero">
      <div className="page-hero-copy">
        {eyebrow && <div className="page-hero-eyebrow">{eyebrow}</div>}
        <div className="page-title page-hero-title">{title}</div>
        {subtitle && <div className="page-sub page-hero-sub">{subtitle}</div>}
      </div>

      <div className="page-hero-aside">
        {actions && <div className="toolbar page-hero-actions">{actions}</div>}
        {stats && stats.length > 0 && (
          <div className="page-hero-stats">
            {stats.map((stat) => (
              <div key={stat.label} className="page-hero-stat">
                <div className="page-hero-stat-label">{stat.label}</div>
                <div className="page-hero-stat-value">{stat.value}</div>
                {stat.hint && <div className="page-hero-stat-hint">{stat.hint}</div>}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
