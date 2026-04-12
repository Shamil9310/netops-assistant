import { Sidebar } from "@/components/sidebar";
import { WorkTimerWorkspace } from "@/components/work-timer-workspace";
import { PageHero } from "@/components/page-hero";
import { getWorkTimerTasks } from "@/lib/api";
import { requireUser } from "@/lib/auth";

export default async function WorkTimerPage() {
  const user = await requireUser();
  const tasks = (await getWorkTimerTasks()) ?? [];
  const initialTaskId = tasks[0]?.id ?? "";

  return (
    <div className="shell">
      <Sidebar user={user} />

      <main className="content-col">
        <PageHero
          eyebrow="Фокус"
          title="Рабочий таймер"
          subtitle="Номер заявки, старт, пауза, продолжение и закрытие в журнал."
        />

        <WorkTimerWorkspace
          tasks={tasks}
          initialTaskId={initialTaskId}
        />
      </main>

      <aside className="filter-col">
        <div className="filter-col-title">Новая заявка</div>
        <div className="focus-note">
          <div className="focus-note-label">Как работает</div>
          <p>Введи номер заявки, добавь задачу, запусти таймер и останови его, когда работа закончена.</p>
        </div>
      </aside>
    </div>
  );
}
