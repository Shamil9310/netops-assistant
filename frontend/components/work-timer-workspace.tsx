"use client";

import { useEffect, useMemo, useState, useTransition, type CSSProperties } from "react";
import { useRouter } from "next/navigation";

import { ConfirmDialog } from "@/components/confirm-dialog";
import type {
  WorkTimerSession,
  WorkTimerTask,
  WorkTimerTaskStatus,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/api-error";

type MutationPayload = Record<string, unknown>;

type Props = {
  tasks: WorkTimerTask[];
  initialTaskId: string;
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

function getSessionLiveSeconds(session: WorkTimerSession, nowTick: number): number {
  const interruptionSeconds = session.interruptions.reduce((total, interruption) => {
    const interruptionEnd = interruption.ended_at ? new Date(interruption.ended_at).getTime() : nowTick;
    return (
      total +
      Math.max(
        0,
        Math.floor((interruptionEnd - new Date(interruption.started_at).getTime()) / 1000),
      )
    );
  }, 0);
  return Math.max(
    0,
    Math.floor((nowTick - new Date(session.started_at).getTime()) / 1000) - interruptionSeconds,
  );
}

function getTaskLiveSeconds(task: WorkTimerTask, nowTick: number): number {
  const activeSession = task.sessions.find((session) => session.ended_at === null);
  if (!activeSession) {
    return task.total_seconds;
  }
  return Math.max(0, task.total_seconds - activeSession.duration_seconds + getSessionLiveSeconds(activeSession, nowTick));
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

export function WorkTimerWorkspace({ tasks, initialTaskId }: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [nowTick, setNowTick] = useState(() => Date.now());
  const [selectedTaskId, setSelectedTaskId] = useState(initialTaskId);
  const [error, setError] = useState<string | null>(null);
  const [newTaskRef, setNewTaskRef] = useState("");
  const [newTaskNote, setNewTaskNote] = useState("");
  const [pendingDelete, setPendingDelete] = useState<WorkTimerTask | null>(null);

  useEffect(() => {
    if (!selectedTaskId) {
      setSelectedTaskId(initialTaskId || tasks[0]?.id || "");
    }
  }, [initialTaskId, selectedTaskId, tasks]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowTick(Date.now());
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const activeTask = useMemo(
    () => tasks.find((task) => task.active_session_id !== null) ?? null,
    [tasks],
  );

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
    if (!newTaskRef.trim()) {
      setError("Номер заявки обязателен");
      return;
    }

    const ok = await submitMutation({
      action: "create_task",
      title: newTaskRef.trim(),
      description: newTaskNote.trim() || null,
      task_ref: newTaskRef.trim(),
      task_url: null,
      tags: [],
      status: "todo",
    });
    if (ok) {
      setNewTaskRef("");
      setNewTaskNote("");
    }
  }

  async function handleTimerAction(taskId: string, timerAction: "start" | "pause" | "resume" | "stop") {
    await submitMutation({
      action: "change_timer",
      task_id: taskId,
      timer_action: timerAction,
    });
  }

  async function handleDeleteTask(task: WorkTimerTask) {
    await submitMutation({ action: "delete_task", task_id: task.id });
    if (selectedTaskId === task.id) {
      setSelectedTaskId("");
    }
  }

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div className="report-tool">
        <div className="filter-group-title">В работе</div>
        {activeTask ? (
          <div className="focus-note">
            <div className="focus-note-label">{activeTask.task_ref || activeTask.title}</div>
            <p>{activeTask.description || "Без описания"}</p>
            <p>{formatDuration(getTaskLiveSeconds(activeTask, nowTick), Boolean(activeTask.active_session_id))}</p>
          </div>
        ) : (
          <div className="focus-note">
            <div className="focus-note-label">Нет активной задачи</div>
            <p>Возьми заявку в работу, чтобы запустить таймер.</p>
          </div>
        )}
      </div>

      <div className="report-tool">
        <div className="filter-group-title">Взять заявку</div>
        <label className="filter-group">
          <span className="filter-date-label">Номер заявки</span>
          <input
            className="filter-date-input"
            value={newTaskRef}
            onChange={(event) => setNewTaskRef(event.target.value)}
            placeholder="INC-12345"
          />
        </label>
        <label className="filter-group">
          <span className="filter-date-label">Комментарий</span>
          <textarea
            className="filter-date-input"
            value={newTaskNote}
            onChange={(event) => setNewTaskNote(event.target.value)}
            placeholder="Коротко: что делаем"
            style={{ minHeight: 78, resize: "vertical" }}
          />
        </label>
        <button type="button" className="btn btn-primary" onClick={handleCreateTask} disabled={isPending}>
          {isPending ? "Создание..." : "Взять в работу"}
        </button>
      </div>

      {error && <div className="form-error">{error}</div>}

      <div className="report-tool">
        <div className="filter-group-title">Заявки</div>
        <div style={{ display: "grid", gap: 8 }}>
          {tasks.map((task) => {
            const taskActiveSession = task.sessions.find((session) => session.ended_at === null) ?? null;
            const statusLabel = getTaskStatusLabel(task.status);
            return (
              <div
                key={task.id}
                style={{
                  padding: "10px 0",
                  borderBottom: "1px solid rgba(170, 185, 205, 0.1)",
                  background: task.id === selectedTaskId ? "rgba(255,255,255,0.02)" : "transparent",
                  display: "grid",
                  gap: 12,
                  cursor: "pointer",
                }}
                onClick={() => setSelectedTaskId(task.id)}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    gap: 12,
                    alignItems: "flex-start",
                  }}
                >
                  <div style={{ display: "grid", gap: 6, minWidth: 0 }}>
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
                      <strong style={{ fontSize: 16 }}>{task.task_ref || task.title}</strong>
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
                  </div>

                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      flexWrap: "wrap",
                      justifyContent: "flex-end",
                      alignItems: "center",
                    }}
                  >
                    <span className="filter-chip" style={inlineChipStyle}>
                      {formatDuration(getTaskLiveSeconds(task, nowTick), Boolean(task.active_session_id))}
                    </span>
                    {!taskActiveSession && (
                      <button type="button" className="btn btn-sm btn-primary" onClick={(event) => {
                        event.stopPropagation();
                        void handleTimerAction(task.id, "start");
                      }}>
                        Старт
                      </button>
                    )}
                    {taskActiveSession?.status === "running" && (
                      <button type="button" className="btn btn-sm" onClick={(event) => {
                        event.stopPropagation();
                        void handleTimerAction(task.id, "pause");
                      }}>
                        Пауза
                      </button>
                    )}
                    {taskActiveSession?.status === "paused" && (
                      <button type="button" className="btn btn-sm" onClick={(event) => {
                        event.stopPropagation();
                        void handleTimerAction(task.id, "resume");
                      }}>
                        Продолжить
                      </button>
                    )}
                    {taskActiveSession && (
                      <button type="button" className="btn btn-sm btn-secondary" onClick={(event) => {
                        event.stopPropagation();
                        void handleTimerAction(task.id, "stop");
                      }}>
                        Закрыть
                      </button>
                    )}
                    <button type="button" className="btn btn-sm btn-danger" onClick={(event) => {
                      event.stopPropagation();
                      setPendingDelete(task);
                    }}>
                      Удалить
                    </button>
                  </div>
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
