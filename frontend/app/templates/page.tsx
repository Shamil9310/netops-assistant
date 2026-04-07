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
        <div className="filter-col-title">Template Engine</div>
        <TemplateControls templates={templates ?? []} />
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Шаблоны</div>
            <div className="page-sub">CRUD шаблонов и применение к планам ночных работ</div>
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
                <div className="plan-sub">{template.category} · key: {template.key} · active: {String(template.is_active)}</div>
                {template.description && <div className="plan-sub" style={{ marginTop: 4 }}>{template.description}</div>}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
