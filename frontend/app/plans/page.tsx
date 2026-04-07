import { Sidebar } from "@/components/sidebar";
import { NightWorkControls } from "@/components/night-work-controls";
import { getNightWorkPlans } from "@/lib/api";
import { requireUser } from "@/lib/auth";

type SearchParams = Record<string, string | string[] | undefined>;

function toSingleValue(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "не задано";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default async function PlansPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const plans = await getNightWorkPlans();

  const planIdFromUrl = toSingleValue(searchParams?.plan_id);
  const selectedPlan = (plans ?? []).find((plan) => plan.id === planIdFromUrl) ?? (plans?.[0] ?? null);

  const blockOptions = (selectedPlan?.blocks ?? []).map((block) => ({ id: block.id, title: block.title }));
  const stepOptions = (selectedPlan?.blocks ?? []).flatMap((block) =>
    block.steps.map((step) => ({ id: step.id, title: step.title, block_id: block.id })),
  );
  const selectedPlanScheduledAtLocal = selectedPlan?.scheduled_at
    ? new Date(selectedPlan.scheduled_at).toISOString().slice(0, 16)
    : "";

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Планирование</div>
        <NightWorkControls
          selectedPlanId={selectedPlan?.id ?? ""}
          selectedPlanTitle={selectedPlan?.title ?? ""}
          selectedPlanDescription={selectedPlan?.description ?? ""}
          selectedPlanScheduledAt={selectedPlanScheduledAtLocal}
          selectedPlanParticipants={selectedPlan?.participants ?? []}
          blocks={blockOptions}
          steps={stepOptions}
        />
      </aside>

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Планы изменений</div>
            <div className="page-sub">Реальные планы ночных работ, блоки SR и шаги исполнения</div>
          </div>
        </div>

        <div className="section-label">Планы</div>
        <div className="plan-list" style={{ marginBottom: 20 }}>
          {(plans ?? []).length === 0 && (
            <div className="plan-item">
              <div className="plan-info">
                <div className="plan-title">Планов пока нет</div>
                <div className="plan-sub">Создай первый план в панели слева.</div>
              </div>
            </div>
          )}
          {(plans ?? []).map((plan) => (
            <a
              key={plan.id}
              className="plan-item"
              href={`/plans?plan_id=${plan.id}`}
              style={plan.id === selectedPlan?.id ? { border: "1px solid var(--green-border)", background: "var(--green-soft)" } : {}}
            >
              <div className="plan-icon bgp">⇄</div>
              <div className="plan-info">
                <div className="plan-title">{plan.title}</div>
                <div className="plan-sub">
                  {plan.status} · scheduled: {formatDateTime(plan.scheduled_at)} · blocks: {plan.blocks.length}
                </div>
              </div>
            </a>
          ))}
        </div>

        {selectedPlan && (
          <>
            <div className="section-label">Детали плана</div>
            <div className="report-block" style={{ marginBottom: 20 }}>
              <div className="report-header">
                <div>
                  <div className="report-header-title">{selectedPlan.title}</div>
                  <div className="report-header-sub">
                    status: {selectedPlan.status} · start: {formatDateTime(selectedPlan.started_at)} · finish: {formatDateTime(selectedPlan.finished_at)}
                  </div>
                  <div className="report-header-sub">
                    participants: {selectedPlan.participants.length > 0 ? selectedPlan.participants.join(", ") : "не указаны"}
                  </div>
                </div>
              </div>
              <pre className="export">{selectedPlan.description ?? "Описание не задано."}</pre>
            </div>

            <div className="section-label">Блоки и шаги</div>
            <div className="plan-list">
              {selectedPlan.blocks.length === 0 && (
                <div className="plan-item">
                  <div className="plan-info">
                    <div className="plan-title">Блоков пока нет</div>
                    <div className="plan-sub">Добавь SR-блок в панели слева.</div>
                  </div>
                </div>
              )}

              {selectedPlan.blocks.map((block) => (
                <div key={block.id} className="plan-item" style={{ flexDirection: "column", alignItems: "stretch" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div className="plan-icon vlan">◻</div>
                    <div className="plan-info">
                      <div className="plan-title">{block.title}</div>
                      <div className="plan-sub">SR: {block.sr_number ?? "не задан"} · status: {block.status}</div>
                    </div>
                  </div>

                  {block.description && <div className="plan-sub" style={{ marginTop: 8 }}>{block.description}</div>}

                  <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
                    {block.steps.length === 0 && (
                      <div className="plan-sub">Шагов пока нет.</div>
                    )}

                    {block.steps.map((step) => (
                      <div key={step.id} className="report-block" style={{ padding: 10 }}>
                        <div className="plan-title">{step.title}</div>
                        <div className="plan-sub">
                          status: {step.status}
                          {step.is_rollback ? " · rollback" : ""}
                          {step.is_post_action ? " · post-action" : ""}
                        </div>
                        {step.description && <div className="plan-sub" style={{ marginTop: 4 }}>{step.description}</div>}
                        {(step.actual_result || step.executor_comment) && (
                          <div className="plan-sub" style={{ marginTop: 4 }}>
                            result: {step.actual_result ?? "—"} · comment: {step.executor_comment ?? "—"}
                          </div>
                        )}
                        {step.collaborators.length > 0 && (
                          <div className="plan-sub" style={{ marginTop: 4 }}>
                            collaborators: {step.collaborators.join(", ")}
                          </div>
                        )}
                        {step.handoff_to && (
                          <div className="plan-sub" style={{ marginTop: 4 }}>
                            handoff: {step.handoff_to}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
