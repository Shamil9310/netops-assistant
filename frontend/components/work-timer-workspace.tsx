"use client";

import { useEffect, useMemo, useState, useTransition, type CSSProperties } from "react";
import { useRouter } from "next/navigation";

import { ConfirmDialog } from "@/components/confirm-dialog";
import type {
  WorkTimerSession,
  WorkTimerTask,
  WorkTimerTaskStatus,
  WorkTimerWeeklySummary,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/api-error";

type MutationPayload = Record<string, unknown>;

type Props = {
  tasks: WorkTimerTask[];
  weeklySummary: WorkTimerWeeklySummary | null;
  initialTaskId: string;
  weekStart: string;
};

function formatDuration(totalSeconds: number, showSeconds = false): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;
  if (showSeconds) {
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  const totalMinutes = Math.floor(safeSeconds / 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return h > 0 ? `${h} ч ${m} мин` : `${m} мин`;
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "не задано";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function formatDateLabel(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    weekday: "short",
  }).format(parsed);
}

function parseTags(text: string): string[] {
  return text
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean)
    .filter((tag, index, list) => list.indexOf(tag) === index);
}

function tagsToText(tags: string[]): string {
  return tags.join(", ");
}

const inlineChipStyle: CSSProperties = {
  pointerEvents: "none",
  width: "auto",
  display: "inline-flex",
};

function getTaskStatusLabel(status: WorkTimerTaskStatus): string {
  const labels: Record<WorkTimerTaskStatus, string> = {
    todo: "К выполнению",
    in_progress: "В работе",
    done: "Готово",
    cancelled: "Отменена",
  };
  return labels[status];
}

function getSessionStatusLabel(status: WorkTimerSession["status"]): string {
  const labels = {
    running: "Запущен",
    paused: "Пауза",
    stopped: "Остановлен",
  } as const;
  return labels[status];
}

async function mutateWorkTimer(
  payload: MutationPayload,
): Promise<{ ok: true } | { ok: false; detail: string }> {
  try {
    const response = await fetch("/api/work-timer/mutate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const responsePayload = await response.json().catch(() => ({}));
    if (!response.ok) {
      return {
        ok: false,
        detail: extractErrorMessage(responsePayload, "Не удалось обновить таймер"),
      };
    }
    return { ok: true };
  } catch {
    return { ok: false, detail: "Ошибка соединения" };
  }
}

export function WorkTimerWorkspace({ tasks, weeklySummary, initialTaskId, weekStart }: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [selectedTaskId, setSelectedTaskId] = useState(initialTaskId);
  const [error, setError] = useState<string | null>(null);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskDescription, setNewTaskDescription] = useState("");
  const [newTaskRef, setNewTaskRef] = useState("");
  const [newTaskUrl, setNewTaskUrl] = useState("");
  const [newTaskTags, setNewTaskTags] = useState("");
  const [pendingDelete, setPendingDelete] = useState<WorkTimerTask | null>(null);

  useEffect(() => {
    if (!selectedTaskId) {
      setSelectedTaskId(initialTaskId || tasks[0]?.id || "");
    }
  }, [initialTaskId, selectedTaskId, tasks]);

  const selectedTask = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? tasks[0] ?? null,
    [selectedTaskId, tasks],
  );

  const activeSession = selectedTask?.sessions.find((session) => session.ended_at === null) ?? null;
  const weeklyInterruptions =
    weeklySummary?.sessions.reduce((total, session) => total + session.interruptions_count, 0) ?? 0;
  const activeTimersCount = tasks.filter((task) => task.active_session_id !== null).length;
  const doneTasksCount = tasks.filter((task) => task.status === "done").length;

  async function submitMutation(payload: MutationPayload) {
    setError(null);
    const mutationResult = await mutateWorkTimer(payload);
    if (!mutationResult.ok) {
      setError(mutationResult.detail);
      return false;
    }
    startTransition(() => router.refresh());
    return true;
  }

  async function handleCreateTask() {
    if (!newTaskTitle.trim()) {
      setError("Название задачи обязательно");
      return;
    }

    const ok = await submitMutation({
      action: "create_task",
      title: newTaskTitle.trim(),
      description: newTaskDescription.trim() || null,
      task_ref: newTaskRef.trim() || null,
      task_url: newTaskUrl.trim() || null,
      tags: parseTags(newTaskTags),
      status: "todo",
    });
    if (ok) {
      setNewTaskTitle("");
      setNewTaskDescription("");
      setNewTaskRef("");
      setNewTaskUrl("");
      setNewTaskTags("");
    }
  }

  async function handleTimerAction(taskId: string, timerAction: "start" | "pause" | "resume" | "stop") {
    await submitMutation({
      action: "change_timer",
      task_id: taskId,
      timer_action: timerAction,
    });
  }

  async function handleToggleDone(task: WorkTimerTask) {
    await submitMutation({
      action: "update_task",
      task_id: task.id,
      status: task.status === "done" ? "todo" : "done",
      completed_at: task.status === "done" ? null : new Date().toISOString(),
    });
  }

  async function handleDeleteTask(task: WorkTimerTask) {
    await submitMutation({ action: "delete_task", task_id: task.id });
    if (selectedTaskId === task.id) {
      setSelectedTaskId("");
    }
  }

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <div className="report-block" style={{ padding: 18 }}>
        <div className="report-header" style={{ marginBottom: 16 }}>
          <div>
            <div className="report-header-title">Рабочий таймер</div>
            <div className="report-header-sub">
              Одна таблица, один активный таймер, теги и отчёт по потраченному времени
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <div className="filter-chip" style={inlineChipStyle}>
              Неделя: {formatDateLabel(weekStart)}
            </div>
            <div className="filter-chip" style={inlineChipStyle}>
              Задач: {tasks.length}
            </div>
            <div className="filter-chip" style={inlineChipStyle}>
              Активных: {activeTimersCount}
            </div>
            <div className="filter-chip" style={inlineChipStyle}>
              Готово: {doneTasksCount}
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 14,
          }}
        >
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge task">Время</div>
            <div
              className="page-title"
              style={{
                fontSize: "2.1rem",
                marginTop: 10,
                WebkitTextFillColor: "initial",
                background: "none",
                color: "var(--text)",
              }}
            >
              {formatDuration(weeklySummary?.total_seconds ?? 0)}
            </div>
            <div className="page-sub">Потрачено за неделю</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge bgp">Сессии</div>
            <div
              className="page-title"
              style={{
                fontSize: "2.1rem",
                marginTop: 10,
                WebkitTextFillColor: "initial",
                background: "none",
                color: "var(--text)",
              }}
            >
              {weeklySummary?.sessions.length ?? 0}
            </div>
            <div className="page-sub">Таймерных запусков</div>
          </div>
          <div className="report-block" style={{ padding: 18 }}>
            <div className="badge acl">Прерывания</div>
            <div
              className="page-title"
              style={{
                fontSize: "2.1rem",
                marginTop: 10,
                WebkitTextFillColor: "initial",
                background: "none",
                color: "var(--text)",
              }}
            >
              {weeklyInterruptions}
            </div>
            <div className="page-sub">За неделю</div>
          </div>
        </div>
      </div>

      <div className="report-block" style={{ padding: 18 }}>
        <div className="report-header" style={{ marginBottom: 12 }}>
          <div>
            <div className="report-header-title">Новая задача</div>
            <div className="report-header-sub">Теги, внешний номер и ссылка на задачу</div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 12,
            alignItems: "end",
          }}
        >
          <label className="filter-group">
            <span className="filter-group-title">Название</span>
            <input
              className="input"
              value={newTaskTitle}
              onChange={(event) => setNewTaskTitle(event.target.value)}
              placeholder="Например, устранить инцидент"
            />
          </label>
          <label className="filter-group">
            <span className="filter-group-title">Описание</span>
            <input
              className="input"
              value={newTaskDescription}
              onChange={(event) => setNewTaskDescription(event.target.value)}
              placeholder="Коротко: что нужно сделать"
            />
          </label>
          <label className="filter-group">
            <span className="filter-group-title">Номер задачи</span>
            <input
              className="input"
              value={newTaskRef}
              onChange={(event) => setNewTaskRef(event.target.value)}
              placeholder="INC-12345"
            />
          </label>
          <label className="filter-group">
            <span className="filter-group-title">Ссылка</span>
            <input
              className="input"
              value={newTaskUrl}
              onChange={(event) => setNewTaskUrl(event.target.value)}
              placeholder="https://..."
            />
          </label>
          <label className="filter-group" style={{ gridColumn: "1 / -1" }}>
            <span className="filter-group-title">Теги</span>
            <input
              className="input"
              value={newTaskTags}
              onChange={(event) => setNewTaskTags(event.target.value)}
              placeholder="инцидент, сеть, задача"
            />
          </label>
          <button
            type="button"
            className="btn"
            onClick={handleCreateTask}
            disabled={isPending}
            style={{ justifySelf: "start" }}
          >
            {isPending ? "Создание..." : "Создать задачу"}
          </button>
        </div>
      </div>

      {error && (
        <div className="form-error" style={{ marginTop: -4 }}>
          {error}
        </div>
      )}

      <div className="report-block" style={{ padding: 18 }}>
        <div className="report-header" style={{ marginBottom: 12 }}>
          <div>
            <div className="report-header-title">Задачи</div>
            <div className="report-header-sub">
              Слева список, справа выбранная задача, ниже история сессий
            </div>
          </div>
        </div>

        {/* Список задач нужен как рабочая таблица: отсюда запускаем и останавливаем таймер. */}
        <div style={{ display: "grid", gap: 10 }}>
          {tasks.map((task) => {
            const taskActiveSession = task.sessions.find((session) => session.ended_at === null) ?? null;
            const statusLabel = getTaskStatusLabel(task.status);
            return (
              <div
                key={task.id}
                style={{
                  padding: 14,
                  borderRadius: 18,
                  border: task.id === selectedTaskId ? "1px solid rgba(131, 211, 225, 0.55)" : "1px solid rgba(255,255,255,0.08)",
                  background: task.id === selectedTaskId ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.02)",
                  display: "grid",
                  gap: 12,
                  cursor: "pointer",
                }}
                onClick={() => setSelectedTaskId(task.id)}
              >
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "minmax(0, 1.8fr) minmax(240px, 1fr)",
                    gap: 12,
                    alignItems: "center",
                  }}
                >
                  <div style={{ display: "grid", gap: 6 }}>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                      <strong style={{ fontSize: 18 }}>{task.title}</strong>
                      <span className="filter-chip" style={inlineChipStyle}>
                        {statusLabel}
                      </span>
                      {taskActiveSession && (
                        <span className="filter-chip" style={inlineChipStyle}>
                          {getSessionStatusLabel(taskActiveSession.status)}
                        </span>
                      )}
                    </div>
                    <div className="page-sub" style={{ margin: 0 }}>
                      {task.description || "Без описания"}
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {(task.tags ?? []).map((tag) => (
                        <span
                          key={tag}
                          className="filter-chip"
                          style={{ ...inlineChipStyle, paddingInline: 10 }}
                        >
                          #{tag}
                        </span>
                      ))}
                      {task.task_ref && (
                        <span className="filter-chip" style={inlineChipStyle}>
                          {task.task_ref}
                        </span>
                      )}
                      {!task.task_ref && <span className="page-sub">без номера</span>}
                    </div>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
                      gap: 8,
                    }}
                  >
                    <div className="focus-note" style={{ margin: 0 }}>
                      <div className="focus-note-label">Время</div>
                      <p>{formatDuration(task.total_seconds)}</p>
                    </div>
                    <div className="focus-note" style={{ margin: 0 }}>
                      <div className="focus-note-label">Паузы</div>
                      <p>{task.interruptions_count}</p>
                    </div>
                    <div className="focus-note" style={{ margin: 0 }}>
                      <div className="focus-note-label">Ссылка</div>
                      <p>{task.task_url ? "Есть" : "Нет"}</p>
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "flex-end" }}>
                      {!taskActiveSession && (
                        <button
                          type="button"
                          className="btn btn-sm"
                          onClick={(event) => {
                            event.stopPropagation();
                            void handleTimerAction(task.id, "start");
                          }}
                        >
                          Старт
                        </button>
                      )}
                      {taskActiveSession?.status === "running" && (
                        <button
                          type="button"
                          className="btn btn-sm"
                          onClick={(event) => {
                            event.stopPropagation();
                            void handleTimerAction(task.id, "pause");
                          }}
                        >
                          Пауза
                        </button>
                      )}
                      {taskActiveSession?.status === "paused" && (
                        <button
                          type="button"
                          className="btn btn-sm"
                          onClick={(event) => {
                            event.stopPropagation();
                            void handleTimerAction(task.id, "resume");
                          }}
                        >
                          Продолжить
                        </button>
                      )}
                      {taskActiveSession && (
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={(event) => {
                            event.stopPropagation();
                            void handleTimerAction(task.id, "stop");
                          }}
                        >
                          Стоп
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={(event) => {
                          event.stopPropagation();
                          void handleToggleDone(task);
                        }}
                      >
                        {task.status === "done" ? "Вернуть" : "Готово"}
                      </button>
                      <button
                        type="button"
                        className="btn btn-sm btn-danger"
                        onClick={(event) => {
                          event.stopPropagation();
                          setPendingDelete(task);
                        }}
                      >
                        Удалить
                      </button>
                    </div>
                  </div>
                </div>

                <div className="page-sub" style={{ margin: 0 }}>
                  Последняя сессия:{" "}
                  {task.sessions.length > 0
                    ? formatDateTime(task.sessions[task.sessions.length - 1]?.started_at ?? null)
                    : "ещё не было"}
                </div>
              </div>
            );
          })}

          {tasks.length === 0 && (
            <div className="focus-note">
              <div className="focus-note-label">Нет задач</div>
              <p>Создай первую рабочую задачу и запусти таймер.</p>
            </div>
          )}
        </div>
      </div>

      {selectedTask && (
        <div className="report-block" style={{ padding: 18 }}>
          <div className="report-header" style={{ marginBottom: 12 }}>
            <div>
              <div className="report-header-title">Выбранная задача</div>
              <div className="report-header-sub">
                {selectedTask.title} · {selectedTask.task_ref ?? "без номера"} ·{" "}
                {formatDuration(selectedTask.total_seconds)}
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span className="filter-chip" style={inlineChipStyle}>
                {selectedTask.active_session_id ? "Таймер активен" : "Таймер не активен"}
              </span>
              {activeSession && (
                <span className="filter-chip" style={inlineChipStyle}>
                  {getSessionStatusLabel(activeSession.status)}
                </span>
              )}
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 12,
            }}
          >
            <div className="focus-note" style={{ margin: 0 }}>
              <div className="focus-note-label">Текущая ссылка</div>
              <p>{selectedTask.task_url || "Нет ссылки"}</p>
            </div>
            <div className="focus-note" style={{ margin: 0 }}>
              <div className="focus-note-label">Теги задачи</div>
              <p>{tagsToText(selectedTask.tags) || "Нет тегов"}</p>
            </div>
          </div>

          {/* История выбранной задачи показывает каждую сессию и все прерывания без перехода на другой экран. */}
          <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
            {selectedTask.sessions.map((session) => (
              <div
                key={session.id}
                style={{
                  padding: 14,
                  borderRadius: 16,
                  border: "1px solid rgba(255,255,255,0.08)",
                  background: "rgba(255,255,255,0.02)",
                  display: "grid",
                  gap: 10,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                  <strong>{getSessionStatusLabel(session.status)}</strong>
                  <span className="page-sub" style={{ margin: 0 }}>
                    {formatDateTime(session.started_at)} → {session.ended_at ? formatDateTime(session.ended_at) : "сейчас"}
                  </span>
                </div>
                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <span className="filter-chip" style={inlineChipStyle}>
                    {formatDuration(session.duration_seconds)}
                  </span>
                  <span className="filter-chip" style={inlineChipStyle}>
                    Паузы: {formatDuration(session.interruption_seconds)}
                  </span>
                  <span className="filter-chip" style={inlineChipStyle}>
                    Инт.: {session.interruptions_count}
                  </span>
                </div>
                {session.interruptions.length > 0 && (
                  <div style={{ display: "grid", gap: 6 }}>
                    {session.interruptions.map((interruption) => (
                      <div
                        key={interruption.id}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          gap: 10,
                          flexWrap: "wrap",
                        }}
                      >
                        <span className="page-sub" style={{ margin: 0 }}>
                          {interruption.reason || "Без причины"}
                        </span>
                        <span className="page-sub" style={{ margin: 0 }}>
                          {formatDuration(interruption.duration_seconds)} · {formatDateTime(interruption.started_at)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Подробный недельный отчёт скрыт в details, чтобы не перегружать экран при пустой неделе. */}
      {weeklySummary && (
        <details className="report-block" style={{ padding: 18 }}>
          <summary style={{ cursor: "pointer", fontWeight: 700 }}>
            Недельный отчёт {formatDateLabel(weeklySummary.week_start)} — {formatDateLabel(weeklySummary.week_end)}
          </summary>

          <div style={{ marginTop: 16, display: "grid", gap: 16 }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: 12,
              }}
            >
              {weeklySummary.days.map((day) => (
                <div className="focus-note" key={day.day} style={{ margin: 0 }}>
                  <div className="focus-note-label">{formatDateLabel(day.day)}</div>
                  <p>{formatDuration(day.total_seconds)}</p>
                  <span className="page-sub" style={{ margin: 0 }}>
                    {day.sessions_count} сессий · {day.interruptions_count} пауз
                  </span>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <div className="filter-group-title">Теги</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {weeklySummary.tags.length > 0 ? (
                  weeklySummary.tags.map((tag) => (
                    <span key={tag.tag} className="filter-chip" style={inlineChipStyle}>
                      #{tag.tag} · {formatDuration(tag.total_seconds)} · {tag.sessions_count}
                    </span>
                  ))
                ) : (
                  <span className="page-sub">Пока без теговой статистики</span>
                )}
              </div>
            </div>

            <div style={{ display: "grid", gap: 10 }}>
              <div className="filter-group-title">Задачи</div>
              {weeklySummary.tasks.length > 0 ? (
                weeklySummary.tasks.map((task) => (
                  <div key={task.task_id} className="focus-note" style={{ margin: 0 }}>
                    <div className="focus-note-label">{task.title}</div>
                    <p>{formatDuration(task.total_seconds)}</p>
                    <span className="page-sub" style={{ margin: 0 }}>
                      {task.sessions_count} сессий · {task.interruptions_count} пауз · {tagsToText(task.tags)}
                    </span>
                  </div>
                ))
              ) : (
                <span className="page-sub">За неделю сессий ещё не было</span>
              )}
            </div>
          </div>
        </details>
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Удалить задачу?"
        description="Будут удалены задача и вся история таймера по ней."
        confirmLabel="Удалить"
        onCancel={() => setPendingDelete(null)}
        onConfirm={async () => {
          if (!pendingDelete) {
            return;
          }
          const task = pendingDelete;
          setPendingDelete(null);
          await handleDeleteTask(task);
        }}
        isSubmitting={isPending}
      />
    </div>
  );
}
