"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import type { JournalActivityStatus } from "@/lib/api";

type Props = {
  entryId: string;
  ticketNumber: string | null;
  activityType: string;
  status: JournalActivityStatus;
  workDate: string;
  startedAt: string | null;
  endedAt: string | null;
  endedDate: string | null;
  description: string | null;
  resolution: string | null;
  contact: string | null;
  taskUrl: string | null;
  onClose: () => void;
};

const STATUS_LABELS: Record<JournalActivityStatus, string> = {
  open: "Открыта",
  in_progress: "В работе",
  closed: "Закрыта",
  cancelled: "Отменена",
};

const STATUS_COLORS: Record<JournalActivityStatus, string> = {
  open: "var(--amber)",
  in_progress: "var(--blue)",
  closed: "var(--green)",
  cancelled: "var(--text-3)",
};

const ALLOWED_TRANSITIONS: Record<JournalActivityStatus, JournalActivityStatus[]> = {
  open: ["in_progress", "closed", "cancelled"],
  in_progress: ["closed", "cancelled"],
  closed: [],
  cancelled: [],
};

export function JournalEntryModal({
  entryId,
  ticketNumber,
  activityType,
  status,
  workDate,
  startedAt,
  endedAt,
  endedDate,
  description,
  resolution,
  contact,
  taskUrl,
  onClose,
}: Props) {
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [editDescription, setEditDescription] = useState(description ?? "");
  const [editResolution, setEditResolution] = useState(resolution ?? "");
  const [editContact, setEditContact] = useState(contact ?? "");
  const [editTaskUrl, setEditTaskUrl] = useState(taskUrl ?? "");
  const [editStatus, setEditStatus] = useState<JournalActivityStatus>(status);
  const [editStartedAt, setEditStartedAt] = useState(startedAt ? startedAt.slice(11, 16) : "");
  const [editEndedAt, setEditEndedAt] = useState(endedAt ? endedAt.slice(11, 16) : "");
  const [editEndedDate, setEditEndedDate] = useState(endedDate ?? workDate);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasCrossMidnightRange = Boolean(
    editStartedAt && editEndedAt && editEndedDate === workDate && editEndedAt < editStartedAt,
  );

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function onSave() {
    setError(null);
    setIsLoading(true);

    if (editEndedDate < workDate) {
      setError("Дата окончания не может быть раньше рабочей даты");
      setIsLoading(false);
      return;
    }

    // В модалке действуют те же правила, что и при создании записи:
    // для одной даты окончание не может быть раньше начала.
    if (hasCrossMidnightRange) {
      setError("Время окончания не может быть раньше времени начала");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`/api/journal/entries/${entryId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: editStatus,
          description: editDescription || null,
          resolution: editResolution || null,
          contact: editContact || null,
          task_url: editTaskUrl || null,
          started_at: editStartedAt || null,
          ended_at: editEndedAt || null,
          ended_date: editEndedAt ? editEndedDate : null,
        }),
      });
      if (!response.ok) {
        const responsePayload = (await response.json()) as { detail?: string };
        setError(responsePayload.detail ?? "Ошибка обновления");
        return;
      }
      setIsEditing(false);
      router.refresh();
      onClose();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsLoading(false);
    }
  }

  async function onQuickStatusChange(newStatus: JournalActivityStatus) {
    setIsLoading(true);
    setError(null);
    try {
      // Быстрое изменение статуса не меняет остальные поля записи
      // и используется как короткое действие прямо из карточки.
      const response = await fetch(`/api/journal/entries/${entryId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!response.ok) {
        const responsePayload = (await response.json()) as { detail?: string };
        setError(responsePayload.detail ?? "Ошибка обновления статуса");
        return;
      }
      router.refresh();
      onClose();
    } catch {
      setError("Ошибка соединения");
    } finally {
      setIsLoading(false);
    }
  }

  const formatClockTime = (timeValue: string | null) =>
    timeValue ? timeValue.slice(0, 5) : "—";
  const transitions = ALLOWED_TRANSITIONS[status];

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal">
        <div className="modal-header">
          <div>
            <div className="modal-sr">{ticketNumber ?? activityType}</div>
            <div className="modal-meta" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span>{activityType}</span>
              <span>·</span>
              <span style={{ color: STATUS_COLORS[status], fontWeight: 600 }}>{STATUS_LABELS[status]}</span>
              <span>·</span>
              <span>{formatClockTime(startedAt)}–{formatClockTime(endedAt)}</span>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {transitions.length > 0 && !isEditing && (
            <div>
              <div className="modal-field-label">Перевести в статус</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {transitions.map((s) => (
                  <button
                    key={s}
                    className="btn btn-sm"
                    style={{ borderColor: STATUS_COLORS[s], color: STATUS_COLORS[s] }}
                    onClick={() => onQuickStatusChange(s)}
                    disabled={isLoading}
                  >
                    {STATUS_LABELS[s]}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <div className="modal-field-label">Время</div>
            {!isEditing && (
              <div className="modal-field-hint">
                Для той же даты время окончания не должно быть раньше времени начала.
              </div>
            )}
            {isEditing ? (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  <input
                    type="time"
                    className="filter-date-input"
                    value={editStartedAt}
                    onChange={(e) => setEditStartedAt(e.target.value)}
                    style={{ marginBottom: 0 }}
                  />
                  <input
                    type="time"
                    className="filter-date-input"
                    value={editEndedAt}
                    onChange={(e) => setEditEndedAt(e.target.value)}
                    style={{ marginBottom: 0 }}
                  />
                </div>
                <input
                  type="date"
                  className="filter-date-input"
                  value={editEndedDate}
                  onChange={(e) => setEditEndedDate(e.target.value)}
                  style={{ marginBottom: 0, marginTop: 8 }}
                />
                {hasCrossMidnightRange && (
                  <div className="focus-note" style={{ marginTop: 10 }}>
                    <div className="focus-note-label">Предупреждение</div>
                    <p>
                      Для той же даты время окончания не может быть раньше
                      времени начала. Если задача закрыта на следующий день,
                      укажи другую дату окончания.
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="modal-field-text">
                {workDate === (endedDate ?? workDate)
                  ? `${formatClockTime(startedAt)}–${formatClockTime(endedAt)}`
                  : `${workDate} ${formatClockTime(startedAt)} → ${endedDate ?? workDate} ${formatClockTime(endedAt)}`}
              </div>
            )}
          </div>

          <div>
            <div className="modal-field-label">Ссылка на задачу</div>
            {!isEditing && (
              <div className="modal-field-hint">Ссылка на BPM, SR, карточку заявки или внешний источник задачи.</div>
            )}
            {isEditing ? (
              <input
                className="filter-date-input"
                value={editTaskUrl}
                onChange={(e) => setEditTaskUrl(e.target.value)}
                placeholder="https://..."
                style={{ marginBottom: 0 }}
              />
            ) : (
              taskUrl ? (
                <a
                  className="modal-field-text"
                  href={taskUrl}
                  target="_blank"
                  rel="noreferrer"
                  style={{ wordBreak: "break-all" }}
                >
                  {taskUrl}
                </a>
              ) : (
                <div className="modal-field-empty">Не заполнено</div>
              )
            )}
          </div>

          <div>
            <div className="modal-field-label">Контакт</div>
            {!isEditing && (
              <div className="modal-field-hint">От кого пришла задача — имя, отдел, email или телефон.</div>
            )}
            {isEditing ? (
              <input
                className="filter-date-input"
                value={editContact}
                onChange={(e) => setEditContact(e.target.value)}
                placeholder="Имя, отдел, email или телефон"
                style={{ marginBottom: 0 }}
              />
            ) : (
              contact
                ? <div className="modal-field-text">{contact}</div>
                : <div className="modal-field-empty">Не заполнено</div>
            )}
          </div>

          <div>
            <div className="modal-field-label">Описание</div>
            {!isEditing && (
              <div className="modal-field-hint">Суть задачи или заявки — что нужно было сделать, от кого пришла, контекст.</div>
            )}
            {isEditing ? (
              <textarea
                className="filter-date-input"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                rows={4}
                placeholder="Суть задачи или заявки — что нужно было сделать, от кого пришла, контекст."
                style={{ marginBottom: 0 }}
              />
            ) : (
              description
                ? <div className="modal-field-text">{description}</div>
                : <div className="modal-field-empty">Не заполнено</div>
            )}
          </div>

          <div>
            <div className="modal-field-label">Решение</div>
            {!isEditing && (
              <div className="modal-field-hint">Что было сделано для решения — команды, настройки, шаги. Заполняй при закрытии.</div>
            )}
            {isEditing ? (
              <textarea
                className="filter-date-input"
                value={editResolution}
                onChange={(e) => setEditResolution(e.target.value)}
                rows={4}
                placeholder="Что было сделано для решения — команды, настройки, шаги."
                style={{ marginBottom: 0 }}
              />
            ) : (
              resolution
                ? <div className="modal-field-text">{resolution}</div>
                : <div className="modal-field-empty">Не заполнено</div>
            )}
          </div>

          {isEditing && (
            <div>
              <div className="modal-field-label">Статус</div>
              <select
                className="filter-date-input"
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value as JournalActivityStatus)}
                style={{ marginBottom: 0 }}
              >
                <option value="open">Открыта</option>
                <option value="in_progress">В работе</option>
                <option value="closed">Закрыта</option>
                <option value="cancelled">Отменена</option>
              </select>
            </div>
          )}

          {error && <div className="form-error">{error}</div>}
        </div>

        <div className="modal-footer">
          {isEditing ? (
            <>
              <button
                className="btn btn-sm"
                onClick={() => {
                  setIsEditing(false);
                  setEditStatus(status);
                  setEditDescription(description ?? "");
                  setEditResolution(resolution ?? "");
                  setEditContact(contact ?? "");
                  setEditTaskUrl(taskUrl ?? "");
                  setEditStartedAt(startedAt ? startedAt.slice(11, 16) : "");
                  setEditEndedAt(endedAt ? endedAt.slice(11, 16) : "");
                  setEditEndedDate(endedDate ?? workDate);
                }}
                disabled={isLoading}
              >
                Отмена
              </button>
              <button className="btn btn-sm btn-primary" onClick={onSave} disabled={isLoading}>
                {isLoading ? "Сохранение..." : "Сохранить"}
              </button>
            </>
          ) : (
            <>
              <button className="btn btn-sm" onClick={onClose}>
                Закрыть
              </button>
              <button className="btn btn-sm btn-primary" onClick={() => setIsEditing(true)}>
                Редактировать
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
