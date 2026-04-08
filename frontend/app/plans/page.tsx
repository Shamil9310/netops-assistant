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

function formatDateTimeLabel(dateTimeValue: string | null): string {
  if (!dateTimeValue) {
    return "не задано";
  }
  const parsedDate = new Date(dateTimeValue);
  if (Number.isNaN(parsedDate.getTime())) {
    return dateTimeValue;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsedDate);
}

export default async function PlansPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const plans = await getNightWorkPlans();

  const planIdFromUrl = toSingleValue(searchParams?.plan_id);
  const activePlan =
    (plans ?? []).find((plan) => plan.id === planIdFromUrl) ?? (plans?.[0] ?? null);

  const blockOptions = (activePlan?.blocks ?? []).map((block) => ({ id: block.id, title: block.title }));
  const stepOptions = (activePlan?.blocks ?? []).flatMap((block) =>
    block.steps.map((step) => ({ id: step.id, title: step.title, block_id: block.id })),
  );
  const activePlanScheduledAtLocal = activePlan?.scheduled_at
    ? new Date(activePlan.scheduled_at).toISOString().slice(0, 16)
    : "";

  return (
    <div className="shell">
      <Sidebar user={user} />

      <aside className="filter-col">
        <div className="filter-col-title">Планирование</div>
        <NightWorkControls
          selectedPlanId={activePlan?.id ?? ""}
          selectedPlanTitle={activePlan?.title ?? ""}
          selectedPlanDescription={activePlan?.description ?? ""}
          selectedPlanScheduledAt={activePlanScheduledAtLocal}
          selectedPlanParticipants={activePlan?.participants ?? []}
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
              style={plan.id === activePlan?.id ? { border: "1px solid var(--green-border)", background: "var(--green-soft)" } : {}}
            >
              <div className="plan-icon bgp">⇄</div>
              <div className="plan-info">
                <div className="plan-title">{plan.title}</div>
                <div className="plan-sub">
                  {plan.status} · запланировано: {formatDateTimeLabel(plan.scheduled_at)} · блоков: {plan.blocks.length}
                </div>
              </div>
            </a>
          ))}
        </div>

        {activePlan && (
          <>
            <div className="section-label">Детали плана</div>
            <div className="report-block" style={{ marginBottom: 20 }}>
              <div className="report-header">
                <div>
                  <div className="report-header-title">{activePlan.title}</div>
                  <div className="report-header-sub">
                    статус: {activePlan.status} · старт: {formatDateTimeLabel(activePlan.started_at)} · завершение: {formatDateTimeLabel(activePlan.finished_at)}
                  </div>
                  <div className="report-header-sub">
                    участники: {activePlan.participants.length > 0 ? activePlan.participants.join(", ") : "не указаны"}
                  </div>
                </div>
              </div>
              <pre className="export">{activePlan.description ?? "Описание не задано."}</pre>
            </div>

            <div className="section-label">Блоки и шаги</div>
            <div className="plan-list">
              {activePlan.blocks.length === 0 && (
                <div className="plan-item">
                  <div className="plan-info">
                    <div className="plan-title">Блоков пока нет</div>
                    <div className="plan-sub">Добавь SR-блок в панели слева.</div>
                  </div>
                </div>
              )}

              {activePlan.blocks.map((block) => (
                <div key={block.id} className="plan-item" style={{ flexDirection: "column", alignItems: "stretch" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div className="plan-icon vlan">◻</div>
                    <div className="plan-info">
                      <div className="plan-title">{block.title}</div>
                      <div className="plan-sub">SR: {block.sr_number ?? "не задан"} · статус: {block.status}</div>
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
                          статус: {step.status}
                          {step.is_rollback ? " · откат" : ""}
                          {step.is_post_action ? " · пост-действие" : ""}
                        </div>
                        {step.description && <div className="plan-sub" style={{ marginTop: 4 }}>{step.description}</div>}
                        {(step.actual_result || step.executor_comment) && (
                          <div className="plan-sub" style={{ marginTop: 4 }}>
                            результат: {step.actual_result ?? "—"} · комментарий: {step.executor_comment ?? "—"}
                          </div>
                        )}
                        {step.collaborators.length > 0 && (
                          <div className="plan-sub" style={{ marginTop: 4 }}>
                            участники: {step.collaborators.join(", ")}
                          </div>
                        )}
                        {step.handoff_to && (
                          <div className="plan-sub" style={{ marginTop: 4 }}>
                            передано: {step.handoff_to}
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
