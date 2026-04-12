import type { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
};

export function CollapsiblePanel({
  title,
  subtitle,
  children,
  defaultOpen = false,
  className = "",
}: Props) {
  return (
    <details className={`collapsible-panel ${className}`.trim()} open={defaultOpen}>
      <summary className="collapsible-panel-summary">
        <div>
          <div className="collapsible-panel-title">{title}</div>
          {subtitle && <div className="collapsible-panel-subtitle">{subtitle}</div>}
        </div>
        <span className="collapsible-panel-chevron" aria-hidden="true">
          ▾
        </span>
      </summary>
      <div className="collapsible-panel-body">{children}</div>
    </details>
  );
}
