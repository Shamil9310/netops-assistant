import { Sidebar } from "@/components/sidebar";
import { WorkTimerWorkspace } from "@/components/work-timer-workspace";
import { getWorkTimerTasks, getWorkTimerWeeklySummary } from "@/lib/api";
import { requireUser } from "@/lib/auth";

function getWeekMonday(dateValue: Date): string {
  const monday = new Date(dateValue);
  const day = monday.getUTCDay();
  const offset = day === 0 ? -6 : 1 - day;
  monday.setUTCDate(monday.getUTCDate() + offset);
  return monday.toISOString().slice(0, 10);
}

export default async function WorkTimerPage() {
  const user = await requireUser();
  const tasks = (await getWorkTimerTasks()) ?? [];
  const weekStart = getWeekMonday(new Date());
  const weeklySummary = await getWorkTimerWeeklySummary(weekStart);
  const initialTaskId = tasks[0]?.id ?? "";

  return (
    <div className="shell shell-two-col">
      <Sidebar user={user} />

      <main className="content-col">
        <div className="page-header">
          <div>
            <div className="page-title">Рабочий таймер</div>
            <div className="page-sub">
              Теги, привязка к задачам, паузы и недельный отчёт по времени
            </div>
          </div>
        </div>

        <WorkTimerWorkspace
          tasks={tasks}
          weeklySummary={weeklySummary}
          initialTaskId={initialTaskId}
          weekStart={weekStart}
        />
      </main>
    </div>
  );
}
