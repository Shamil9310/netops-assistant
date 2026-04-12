import { Sidebar } from "@/components/sidebar";
import { StudyWorkspace } from "@/components/study-workspace";
import { PageHero } from "@/components/page-hero";
import { getStudyPlans, getStudyWeeklySummary } from "@/lib/api";
import { requireUser } from "@/lib/auth";

function getWeekMonday(dateValue: Date): string {
  const monday = new Date(dateValue);
  const day = monday.getUTCDay();
  const offset = day === 0 ? -6 : 1 - day;
  monday.setUTCDate(monday.getUTCDate() + offset);
  return monday.toISOString().slice(0, 10);
}

export default async function StudyPage() {
  const user = await requireUser();
  const plans = (await getStudyPlans()) ?? [];
  const weekStart = getWeekMonday(new Date());
  const weeklySummary = await getStudyWeeklySummary(weekStart);
  const initialPlanId = plans[0]?.id ?? "";

  return (
    <div className="shell shell-two-col">
      <Sidebar user={user} />

      <main className="content-col">
        <PageHero
          eyebrow="План развития"
          title="Учёба"
          subtitle="Учебные планы, чекпоинты, чеклист и учёт времени по сессиям."
          stats={[
            { label: "Планов", value: String(plans.length), hint: "В каталоге" },
            { label: "Неделя", value: weekStart, hint: "Старт периода" },
            { label: "Активный", value: plans[0]?.title ?? "—", hint: "Стартовый план" },
            { label: "Сессии", value: String(weeklySummary?.sessions.length ?? 0), hint: "За неделю" },
          ]}
        />

        <StudyWorkspace
          plans={plans}
          weeklySummary={weeklySummary}
          initialPlanId={initialPlanId}
          weekStart={weekStart}
        />
      </main>
    </div>
  );
}
