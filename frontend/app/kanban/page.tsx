import { Sidebar } from "@/components/sidebar";
import { NightWorkControls } from "@/components/night-work-controls";
import { PlanKanbanWorkspace } from "@/components/plan-kanban-workspace";
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

export default async function KanbanPage({ searchParams }: { searchParams?: SearchParams }) {
  const user = await requireUser();
  const plans = await getNightWorkPlans();

  const planIdFromUrl = toSingleValue(searchParams?.plan_id);
  const activePlan = (plans ?? []).find((plan) => plan.id === planIdFromUrl) ?? (plans?.[0] ?? null);

  const blockOptions = (activePlan?.blocks ?? []).map((block) => ({ id: block.id, title: block.title }));
  const stepOptions = (activePlan?.blocks ?? []).flatMap((block) =>
    block.steps.map((step) => ({ id: step.id, title: step.title, block_id: block.id })),
  );
  const activePlanScheduledAtLocal = activePlan?.scheduled_at
    ? new Date(activePlan.scheduled_at).toISOString().slice(0, 16)
    : "";

  return (
    <div className="shell shell-two-col">
      <Sidebar user={user} />

      <main className="content-col">
        <div className="report-block" style={{ padding: 18 }}>
          <div className="report-header" style={{ marginBottom: 16 }}>
            <div>
              <div className="report-header-title">Планирование</div>
              <div className="report-header-sub">Управление ночными работами остаётся в основном рабочем поле, без третьей колонки.</div>
            </div>
          </div>

          <NightWorkControls
            selectedPlanId={activePlan?.id ?? ""}
            selectedPlanTitle={activePlan?.title ?? ""}
            selectedPlanDescription={activePlan?.description ?? ""}
            selectedPlanScheduledAt={activePlanScheduledAtLocal}
            selectedPlanParticipants={activePlan?.participants ?? []}
            blocks={blockOptions}
            steps={stepOptions}
          />
        </div>

        <PlanKanbanWorkspace plans={plans ?? []} initialPlanId={activePlan?.id ?? ""} />

        {activePlan && (
          <div className="page-sub" style={{ marginTop: -4 }}>
            Текущая карточка: {activePlan.title} · {activePlan.status} · старт {formatDateTimeLabel(activePlan.started_at)}
          </div>
        )}
      </main>
    </div>
  );
}
