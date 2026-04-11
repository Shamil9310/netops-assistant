import { Sidebar } from "@/components/sidebar";
import { TemplateControls } from "@/components/template-controls";
import { getPlanTemplates } from "@/lib/api";
import { requireUser } from "@/lib/auth";

export default async function TemplatesPage() {
  const user = await requireUser();
  const templates = await getPlanTemplates();

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Шаблоны</div>
        <TemplateControls templates={templates ?? []} />
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Шаблоны</div>
            <div className="page-sub">Управление шаблонами и применение к планам ночных работ</div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Шаблонов</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {(templates ?? []).length}
            </div>
            <div className="page-sub">В библиотеке</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge bgp">Состояние</div>
            <div className="page-title" style={{ fontSize: "2.2rem", marginTop: 10, WebkitTextFillColor: "initial", background: "none", color: "var(--text)" }}>
              {templates?.some((template) => template.is_active) ? "active" : "—"}
            </div>
            <div className="page-sub">Есть активные шаблоны</div>
          </div>
        </div>

        <div className="section-label">Библиотека шаблонов</div>
        <div className="plan-list">
          {(templates ?? []).length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Шаблоны отсутствуют</div>
                <div className="plan-sub">Создай первый шаблон в панели слева.</div>
              </div>
            </div>
          )}

          {(templates ?? []).map((template) => (
            <div key={template.id} className="plan-item">
              <div className="plan-icon bgp">◎</div>
              <div className="plan-info">
                <div className="plan-title">{template.name}</div>
                <div className="plan-sub">{template.category} · ключ: {template.key} · активен: {template.is_active ? "да" : "нет"}</div>
                {template.description && <div className="plan-sub" style={{ marginTop: 4 }}>{template.description}</div>}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
