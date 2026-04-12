"use client";

import { useEffect, useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import type {
  StudyCheckpoint,
  StudyModule,
  StudyPlan,
  StudyPlanTrack,
  StudySession,
  StudyWeeklySummary,
} from "@/lib/api";
import { extractErrorMessage } from "@/lib/api-error";

type MutationPayload = Record<string, unknown>;

// Форматирует длительность в секундах в читаемый вид (ч мин сек).
function formatDuration(totalSeconds: number, showSeconds = false): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(s / 3600);
  const minutes = Math.floor((s % 3600) / 60);
  const seconds = s % 60;
  if (showSeconds) {
    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  }
  const totalMinutes = Math.floor(s / 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return h > 0 ? `${h} ч ${m} мин` : `${m} мин`;
}

// Форматирует дату/время из ISO-строки в локаль ru-RU.
function formatDateTime(value: string | null): string {
  if (!value) return "не задано";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

// Учебные треки: ключ, название и краткое описание.
const STUDY_TRACKS: Array<{ key: StudyPlanTrack; label: string }> = [
  { key: "python", label: "Python" },
  { key: "networks", label: "Сети" },
];

function getTrackLabel(track: StudyPlanTrack): string {
  return STUDY_TRACKS.find((item) => item.key === track)?.label ?? track;
}

// Единая точка входа для всех мутаций — не плодим отдельные маршруты на каждую кнопку.
async function mutateStudy(
  payload: MutationPayload,
): Promise<{ ok: true } | { ok: false; detail: string }> {
  try {
    const response = await fetch("/api/study/mutate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const responsePayload = await response.json().catch(() => ({}));
    if (!response.ok) {
      return {
        ok: false,
        detail: extractErrorMessage(responsePayload, "Не удалось обновить данные обучения"),
      };
    }
    return { ok: true };
  } catch {
    return { ok: false, detail: "Ошибка соединения" };
  }
}

function getPlanStudySeconds(plan: StudyPlan, checkpointId: string): number {
  return plan.sessions
    .filter((session) => session.checkpoint_id === checkpointId)
    .reduce((total, session) => total + session.duration_seconds, 0);
}

type Props = {
  plans: StudyPlan[];
  weeklySummary: StudyWeeklySummary | null;
  initialPlanId: string;
  weekStart: string;
};

export function StudyWorkspace({
  plans,
  weeklySummary,
  initialPlanId,
  weekStart,
}: Props) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [selectedTrack, setSelectedTrack] = useState<StudyPlanTrack>(() => {
    const initialPlan = plans.find((plan) => plan.id === initialPlanId);
    return initialPlan?.track ?? plans[0]?.track ?? "python";
  });
  const [selectedPlanId, setSelectedPlanId] = useState(initialPlanId);
  const [error, setError] = useState<string | null>(null);
  const [newPlanTitle, setNewPlanTitle] = useState("");
  const [newPlanDescription, setNewPlanDescription] = useState("");
  const [newCheckpointTitle, setNewCheckpointTitle] = useState("");
  const [newCheckpointDescription, setNewCheckpointDescription] = useState("");
  const [stopPercent, setStopPercent] = useState("50");
  const [showAddPlan, setShowAddPlan] = useState(false);
  // "single" — одна тема, "roadmap" — список тем построчно
  const [addTopicMode, setAddTopicMode] = useState<"hidden" | "single" | "roadmap">("hidden");
  const [roadmapText, setRoadmapText] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const selectedPlan = useMemo(
    () =>
      plans.find((plan) => plan.track === selectedTrack && plan.id === selectedPlanId) ??
      plans.find((plan) => plan.track === selectedTrack) ??
      null,
    [plans, selectedPlanId, selectedTrack],
  );

  const trackPlans = useMemo(
    () => plans.filter((plan) => plan.track === selectedTrack),
    [plans, selectedTrack],
  );

  const activeSession = useMemo(
    () => selectedPlan?.sessions.find((session) => session.ended_at === null) ?? null,
    [selectedPlan],
  );
  const activeCheckpointId = activeSession?.checkpoint_id ?? null;
  const activeCheckpoint = useMemo(() => {
    if (!selectedPlan || !activeCheckpointId) return null;
    return selectedPlan.checkpoints.find((cp) => cp.id === activeCheckpointId) ?? null;
  }, [activeCheckpointId, selectedPlan]);

  // Живой таймер — обновляет счётчик каждую секунду пока идёт активная сессия.
  useEffect(() => {
    if (!activeSession?.started_at) {
      setElapsedSeconds(0);
      return;
    }
    const started = new Date(activeSession.started_at).getTime();
    const tick = () => setElapsedSeconds(Math.floor((Date.now() - started) / 1000));
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [activeSession]);

  // При смене активной темы инициализируем stopPercent текущим прогрессом —
  // чтобы пользователь продолжал с того места, где остановился.
  useEffect(() => {
    if (activeCheckpoint) {
      setStopPercent(String(activeCheckpoint.progress_percent));
    }
  }, [activeCheckpoint?.id]);

  const totalWeekSeconds = weeklySummary?.total_seconds ?? 0;

  async function submitMutation(payload: MutationPayload) {
    setError(null);
    const mutationResult = await mutateStudy(payload);
    if (!mutationResult.ok) {
      setError(mutationResult.detail);
      return false;
    }
    startTransition(() => router.refresh());
    return true;
  }

  function handleSelectTrack(track: StudyPlanTrack) {
    setSelectedTrack(track);
    const next = plans.find((plan) => plan.track === track);
    setSelectedPlanId(next?.id ?? "");
  }

  async function handleCreatePlan() {
    if (!newPlanTitle.trim()) {
      setError("Название плана обязательно");
      return;
    }
    const ok = await submitMutation({
      action: "create_plan",
      title: newPlanTitle.trim(),
      description: newPlanDescription.trim() || null,
      track: selectedTrack,
      status: "draft",
    });
    if (ok) {
      setNewPlanTitle("");
      setNewPlanDescription("");
      setShowAddPlan(false);
    }
  }

  async function handleAddCheckpoint() {
    if (!selectedPlan) {
      setError("Сначала выберите план");
      return;
    }
    if (!newCheckpointTitle.trim()) {
      setError("Название темы обязательно");
      return;
    }
    const nextOrder = selectedPlan.checkpoints.length;
    const ok = await submitMutation({
      action: "add_checkpoint",
      plan_id: selectedPlan.id,
      title: newCheckpointTitle.trim(),
      description: newCheckpointDescription.trim() || null,
      order_index: nextOrder,
    });
    if (ok) {
      setNewCheckpointTitle("");
      setNewCheckpointDescription("");
      setAddTopicMode("hidden");
    }
  }

  // Добавляет сразу несколько тем из текстового роадмапа — каждая строка становится отдельной темой.
  // Парсит textarea роадмапа в секции для bulk-запроса.
  // Строки вида "# Название" становятся заголовками модулей.
  // Остальные строки — темы внутри текущей секции.
  function parseRoadmapSections(text: string): Array<{ module_title: string | null; topics: string[] }> {
    const sections: Array<{ module_title: string | null; topics: string[] }> = [];
    let currentSection: { module_title: string | null; topics: string[] } = { module_title: null, topics: [] };

    for (const rawLine of text.split("\n")) {
      const line = rawLine.trim();
      if (!line) continue;

      if (line.startsWith("# ")) {
        if (currentSection.topics.length > 0 || currentSection.module_title !== null) {
          sections.push(currentSection);
        }
        currentSection = { module_title: line.slice(2).trim(), topics: [] };
      } else {
        currentSection.topics.push(line);
      }
    }
    if (currentSection.topics.length > 0 || currentSection.module_title !== null) {
      sections.push(currentSection);
    }
    return sections;
  }

  async function handleAddRoadmap() {
    if (!selectedPlan) {
      setError("Сначала выберите план");
      return;
    }
    const sections = parseRoadmapSections(roadmapText);
    const totalTopics = sections.reduce((sum, s) => sum + s.topics.length, 0);
    if (totalTopics === 0) {
      setError("Роадмап пустой — введите хотя бы одну тему");
      return;
    }
    // Один bulk-запрос вместо N последовательных — атомарно и быстро.
    const ok = await submitMutation({
      action: "bulk_add_checkpoints",
      plan_id: selectedPlan.id,
      sections,
    });
    if (ok) {
      setRoadmapText("");
      setAddTopicMode("hidden");
    }
  }

  async function startCheckpoint(checkpoint: StudyCheckpoint) {
    if (checkpoint.is_done) {
      setError("Эта тема уже завершена");
      return;
    }
    await submitMutation({
      action: "change_timer",
      plan_id: selectedPlan?.id,
      checkpoint_id: checkpoint.id,
      timer_action: "start",
    });
  }

  async function stopCheckpoint(checkpoint: StudyCheckpoint) {
    const parsedPercent = Number.parseInt(stopPercent, 10);
    if (Number.isNaN(parsedPercent) || parsedPercent < 0 || parsedPercent > 100) {
      setError("Введите процент от 0 до 100");
      return;
    }
    await submitMutation({
      action: "change_timer",
      plan_id: selectedPlan?.id,
      checkpoint_id: checkpoint.id,
      timer_action: "stop",
      progress_percent: parsedPercent,
    });
    setStopPercent("0");
  }

  const nextCheckpoint =
    selectedPlan?.checkpoints.find((cp) => !cp.is_done) ?? null;

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {/* ── Шапка с метриками ── */}
      <div className="report-block" style={{ padding: "16px 20px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div>
            <div className="report-header-sub" style={{ letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Учёба
            </div>
            <div className="report-header-title" style={{ fontSize: 22, lineHeight: 1.1 }}>
              Рабочее пространство
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <div className="badge task" style={{ minWidth: 100, justifyContent: "center" }}>
              Неделя&nbsp;<strong>{formatDuration(totalWeekSeconds)}</strong>
            </div>
            <div className="badge bgp" style={{ minWidth: 80, justifyContent: "center" }}>
              Планы&nbsp;<strong>{plans.length}</strong>
            </div>
            <div className="badge acl" style={{ minWidth: 90, justifyContent: "center" }}>
              Завершено&nbsp;<strong>{weeklySummary?.completed_checkpoints.length ?? 0}</strong>
            </div>
          </div>
        </div>
      </div>

      {/* ── Выбор трека + плана ── */}
      <div className="report-block" style={{ padding: "14px 20px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          {/* Треки — pill-табы */}
          <div style={{ display: "flex", gap: 6 }}>
            {STUDY_TRACKS.map((track) => (
              <button
                key={track.key}
                type="button"
                className={selectedTrack === track.key ? "btn btn-primary" : "btn btn-secondary"}
                style={{ minWidth: 80, borderRadius: 24 }}
                onClick={() => handleSelectTrack(track.key)}
              >
                {track.label}
              </button>
            ))}
          </div>

          {/* Планы внутри трека — pill-табы */}
          {trackPlans.length > 0 && (
            <>
              <div
                style={{
                  width: 1,
                  height: 24,
                  background: "rgba(255,255,255,0.12)",
                  margin: "0 4px",
                }}
              />
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {trackPlans.map((plan) => (
                  <div key={plan.id} style={{ display: "flex", alignItems: "center", gap: 2 }}>
                    <button
                      type="button"
                      className={
                        selectedPlan?.id === plan.id ? "btn btn-primary" : "btn btn-secondary"
                      }
                      style={{ borderRadius: 24, fontSize: 13 }}
                      onClick={() => setSelectedPlanId(plan.id)}
                    >
                      {plan.title}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      disabled={isPending}
                      aria-label={`Удалить план ${plan.title}`}
                      style={{
                        borderRadius: 24,
                        fontSize: 13,
                        padding: "4px 8px",
                        opacity: 0.5,
                        lineHeight: 1,
                      }}
                      onClick={async () => {
                        if (!window.confirm(`Удалить план «${plan.title}»? Все темы и сессии будут удалены.`)) return;
                        await submitMutation({ action: "delete_plan", plan_id: plan.id });
                      }}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}

          <div style={{ marginLeft: "auto" }}>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ borderRadius: 24, fontSize: 13 }}
              onClick={() => setShowAddPlan((v) => !v)}
            >
              {showAddPlan ? "Отмена" : "+ Новый план"}
            </button>
          </div>
        </div>

        {/* Форма создания плана */}
        {showAddPlan && (
          <div
            style={{
              marginTop: 12,
              display: "flex",
              gap: 8,
              flexWrap: "wrap",
              alignItems: "flex-end",
            }}
          >
            <label style={{ display: "grid", gap: 4, flex: "2 1 200px" }}>
              <span className="filter-date-label">Название плана · {getTrackLabel(selectedTrack)}</span>
              <input
                className="filter-date-input"
                value={newPlanTitle}
                onChange={(e) => setNewPlanTitle(e.target.value)}
                placeholder={`Например, ${getTrackLabel(selectedTrack).toLowerCase()} за месяц`}
              />
            </label>
            <label style={{ display: "grid", gap: 4, flex: "3 1 260px" }}>
              <span className="filter-date-label">Описание</span>
              <input
                className="filter-date-input"
                value={newPlanDescription}
                onChange={(e) => setNewPlanDescription(e.target.value)}
                placeholder="Кратко что нужно освоить"
              />
            </label>
            <button className="btn btn-primary" type="button" disabled={isPending} onClick={handleCreatePlan}>
              Создать
            </button>
          </div>
        )}
      </div>

      {selectedPlan ? (
        <>
          {/* ── Живой таймер ── */}
          <div
            className="report-block"
            style={{
              padding: "20px 24px",
              background: activeSession
                ? "linear-gradient(135deg, rgba(91,216,211,0.08) 0%, rgba(10,16,27,0.9) 100%)"
                : "rgba(10,16,27,0.9)",
              borderRadius: 24,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 24,
                flexWrap: "wrap",
              }}
            >
              {/* Большой счётчик */}
              <div style={{ flex: "0 0 auto" }}>
                <div className="page-sub" style={{ marginBottom: 4 }}>
                  {activeSession ? "Идёт сессия" : "Таймер остановлен"}
                </div>
                <div
                  style={{
                    fontSize: 52,
                    fontWeight: 700,
                    lineHeight: 1,
                    letterSpacing: "-0.02em",
                    fontVariantNumeric: "tabular-nums",
                    color: activeSession ? "var(--green)" : "rgba(255,255,255,0.35)",
                  }}
                >
                  {formatDuration(elapsedSeconds, true)}
                </div>
              </div>

              {/* Текущая / следующая тема */}
              <div style={{ flex: "1 1 200px" }}>
                {activeCheckpoint ? (
                  <>
                    <div className="page-sub" style={{ marginBottom: 2 }}>Текущая тема</div>
                    <div style={{ fontWeight: 700, fontSize: 18 }}>{activeCheckpoint.title}</div>
                    {activeCheckpoint.description && (
                      <div className="page-sub" style={{ marginTop: 2 }}>
                        {activeCheckpoint.description}
                      </div>
                    )}
                  </>
                ) : nextCheckpoint ? (
                  <>
                    <div className="page-sub" style={{ marginBottom: 2 }}>Следующая тема</div>
                    <div style={{ fontWeight: 600, fontSize: 16, opacity: 0.6 }}>
                      {nextCheckpoint.title}
                    </div>
                  </>
                ) : (
                  <div className="page-sub">Все темы пройдены</div>
                )}
              </div>

              {/* Итого по плану */}
              <div style={{ flex: "0 0 auto", textAlign: "right" }}>
                <div className="page-sub" style={{ marginBottom: 2 }}>Итого по плану</div>
                <div style={{ fontWeight: 700, fontSize: 20 }}>
                  {formatDuration(selectedPlan.total_seconds)}
                </div>
              </div>
            </div>

            {/* Прогресс % при остановке — показываем только для активной сессии */}
            {activeSession && activeCheckpoint && (
              <div
                style={{
                  marginTop: 16,
                  display: "flex",
                  gap: 10,
                  alignItems: "center",
                  flexWrap: "wrap",
                }}
              >
                <span className="filter-date-label">Прогресс по теме, %</span>
                <input
                  className="filter-date-input"
                  type="number"
                  min={0}
                  max={100}
                  value={stopPercent}
                  onChange={(e) => setStopPercent(e.target.value)}
                  style={{ width: 80 }}
                />
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={isPending}
                  onClick={() => stopCheckpoint(activeCheckpoint)}
                  style={{ background: "rgba(255,80,80,0.18)", borderColor: "rgba(255,80,80,0.4)" }}
                >
                  Остановить
                </button>
              </div>
            )}
          </div>

          {/* ── Список тем ── */}
          <div className="report-block" style={{ padding: "18px 20px", borderRadius: 24 }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 14,
                flexWrap: "wrap",
                gap: 8,
              }}
            >
              <div>
                <div className="report-header-sub" style={{ letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  {getTrackLabel(selectedTrack)} · {selectedPlan.title}
                </div>
                {selectedPlan.description && (
                  <div className="page-sub">{selectedPlan.description}</div>
                )}
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <button
                  type="button"
                  className={addTopicMode === "single" ? "btn btn-primary" : "btn btn-secondary"}
                  style={{ borderRadius: 24, fontSize: 13 }}
                  onClick={() => setAddTopicMode(addTopicMode === "single" ? "hidden" : "single")}
                >
                  + Тема
                </button>
                <button
                  type="button"
                  className={addTopicMode === "roadmap" ? "btn btn-primary" : "btn btn-secondary"}
                  style={{ borderRadius: 24, fontSize: 13 }}
                  onClick={() => setAddTopicMode(addTopicMode === "roadmap" ? "hidden" : "roadmap")}
                >
                  + Роадмап
                </button>
              </div>
            </div>

            {/* Форма добавления одной темы */}
            {addTopicMode === "single" && (
              <div
                style={{
                  marginBottom: 16,
                  display: "flex",
                  gap: 8,
                  flexWrap: "wrap",
                  alignItems: "flex-end",
                  padding: "14px 16px",
                  borderRadius: 16,
                  background: "rgba(255,255,255,0.04)",
                }}
              >
                <label style={{ display: "grid", gap: 4, flex: "2 1 200px" }}>
                  <span className="filter-date-label">Название темы</span>
                  <input
                    className="filter-date-input"
                    value={newCheckpointTitle}
                    onChange={(e) => setNewCheckpointTitle(e.target.value)}
                    placeholder="Например, маршрутизация BGP"
                  />
                </label>
                <label style={{ display: "grid", gap: 4, flex: "3 1 280px" }}>
                  <span className="filter-date-label">Описание</span>
                  <input
                    className="filter-date-input"
                    value={newCheckpointDescription}
                    onChange={(e) => setNewCheckpointDescription(e.target.value)}
                    placeholder="Что нужно изучить"
                  />
                </label>
                <button className="btn btn-primary" type="button" disabled={isPending} onClick={handleAddCheckpoint}>
                  Добавить
                </button>
              </div>
            )}

            {/* Форма добавления роадмапа — список тем построчно */}
            {addTopicMode === "roadmap" && (
              <div
                style={{
                  marginBottom: 16,
                  padding: "14px 16px",
                  borderRadius: 16,
                  background: "rgba(255,255,255,0.04)",
                  display: "grid",
                  gap: 10,
                }}
              >
                <div>
                  <span className="filter-date-label">Роадмап — каждая строка станет темой</span>
                  <p className="page-sub" style={{ marginTop: 4 }}>
                    Строки вида <strong># Название</strong> создают модуль (раздел). Остальные строки — темы внутри него.
                  </p>
                </div>
                <textarea
                  className="filter-date-input"
                  value={roadmapText}
                  onChange={(e) => setRoadmapText(e.target.value)}
                  placeholder={"# Раздел 1\nТема 1\nТема 2\n\n# Раздел 2\nТема 3"}
                  rows={8}
                  style={{ resize: "vertical", fontFamily: "inherit" }}
                />
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <button
                    className="btn btn-primary"
                    type="button"
                    disabled={isPending}
                    onClick={handleAddRoadmap}
                  >
                    Добавить все темы
                  </button>
                  <span className="page-sub">
                    {roadmapText.split("\n").filter((l) => l.trim()).length} тем
                  </span>
                </div>
              </div>
            )}

            {/* Список тем, сгруппированный по модулям */}
            {selectedPlan.checkpoints.length === 0 ? (
              <div className="focus-note" style={{ padding: 20 }}>
                <div className="focus-note-label">Пока нет тем</div>
                <p>Нажмите «+ Тема» или «+ Роадмап» чтобы начать заполнять план.</p>
              </div>
            ) : (
              <CheckpointList
                plan={selectedPlan}
                activeCheckpointId={activeCheckpointId}
                activeSession={activeSession}
                isPending={isPending}
                onStart={startCheckpoint}
                onStop={stopCheckpoint}
                onToggleDone={async (checkpoint) => {
                  await submitMutation({
                    action: "update_checkpoint",
                    checkpoint_id: checkpoint.id,
                    is_done: !checkpoint.is_done,
                  });
                }}
                onDeleteCheckpoint={async (checkpoint) => {
                  if (!window.confirm(`Удалить тему «${checkpoint.title}»?`)) return;
                  await submitMutation({ action: "delete_checkpoint", checkpoint_id: checkpoint.id });
                }}
                onDeleteModule={async (module) => {
                  if (!window.confirm(`Удалить модуль «${module.title}»? Темы останутся в плане без модуля.`)) return;
                  await submitMutation({ action: "delete_module", module_id: module.id });
                }}
                getPlanStudySeconds={getPlanStudySeconds}
              />
            )}
          </div>

          {/* ── История сессий ── */}
          {selectedPlan.sessions.length > 0 && (
            <details className="report-block" style={{ padding: "14px 20px" }}>
              <summary className="page-sub" style={{ cursor: "pointer" }}>
                История сессий · {selectedPlan.sessions.length} записей
              </summary>
              <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
                {selectedPlan.sessions.map((session) => {
                  const cpTitle =
                    selectedPlan.checkpoints.find((cp) => cp.id === session.checkpoint_id)?.title ??
                    "Тема";
                  return (
                    <div key={session.id} className="focus-note">
                      <div className="focus-note-label">{cpTitle}</div>
                      <p>
                        {formatDuration(session.duration_seconds)} · {session.progress_percent}% ·{" "}
                        {session.status}
                      </p>
                      <p>
                        {formatDateTime(session.started_at)} — {formatDateTime(session.ended_at)}
                      </p>
                    </div>
                  );
                })}
              </div>
            </details>
          )}
        </>
      ) : (
        <div className="report-block" style={{ padding: 24 }}>
          <div className="focus-note">
            <div className="focus-note-label">Нет плана для трека «{getTrackLabel(selectedTrack)}»</div>
            <p>Нажмите «+ Новый план» и создайте первый учебный план.</p>
          </div>
        </div>
      )}

      {/* ── Итоги недели ── */}
      {weeklySummary && (
        <details className="report-block" style={{ padding: "14px 20px" }}>
          <summary className="page-sub" style={{ cursor: "pointer" }}>
            Итоги недели {weeklySummary.week_start} — {weeklySummary.week_end} ·{" "}
            {formatDuration(weeklySummary.total_seconds)}
          </summary>
          <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
            {weeklySummary.days.map((day) => (
              <div key={day.day} className="focus-note">
                <div className="focus-note-label">{day.day}</div>
                <p>
                  {formatDuration(day.total_seconds)} · {day.sessions_count} сессий
                </p>
              </div>
            ))}
          </div>
        </details>
      )}

      {/* ── Ошибки ── */}
      {error && (
        <div
          className="form-error"
          style={{ position: "sticky", bottom: 16 }}
          role="alert"
        >
          {error}
          <button
            type="button"
            onClick={() => setError(null)}
            style={{
              marginLeft: 12,
              background: "none",
              border: "none",
              color: "inherit",
              cursor: "pointer",
              opacity: 0.7,
            }}
            aria-label="Закрыть ошибку"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

// ── Вспомогательный компонент: список тем, сгруппированный по модулям ──

type CheckpointListProps = {
  plan: StudyPlan;
  activeCheckpointId: string | null;
  activeSession: StudySession | null;
  isPending: boolean;
  onStart: (checkpoint: StudyCheckpoint) => void;
  onStop: (checkpoint: StudyCheckpoint) => void;
  onToggleDone: (checkpoint: StudyCheckpoint) => void;
  onDeleteCheckpoint: (checkpoint: StudyCheckpoint) => void;
  onDeleteModule: (module: StudyModule) => void;
  getPlanStudySeconds: (plan: StudyPlan, checkpointId: string) => number;
};

function CheckpointList({
  plan,
  activeCheckpointId,
  activeSession,
  isPending,
  onStart,
  onStop,
  onToggleDone,
  onDeleteCheckpoint,
  onDeleteModule,
  getPlanStudySeconds,
}: CheckpointListProps) {
  // Группируем темы по module_id. Темы без модуля попадают в группу null.
  const moduleMap = new Map<string | null, StudyCheckpoint[]>();
  moduleMap.set(null, []);
  for (const mod of plan.modules) {
    moduleMap.set(mod.id, []);
  }
  for (const checkpoint of plan.checkpoints) {
    const key = checkpoint.module_id ?? null;
    if (!moduleMap.has(key)) {
      moduleMap.set(key, []);
    }
    moduleMap.get(key)!.push(checkpoint);
  }

  // Порядок отображения: сначала модули по order_index, потом темы без модуля.
  const orderedModules = [...plan.modules].sort((a, b) => a.order_index - b.order_index);
  const unassigned = moduleMap.get(null) ?? [];

  let globalIndex = 0;

  function renderCheckpoint(checkpoint: StudyCheckpoint) {
    const spentSeconds = getPlanStudySeconds(plan, checkpoint.id);
    const isActive = activeCheckpointId === checkpoint.id;
    globalIndex += 1;
    const idx = globalIndex;

    return (
      <div
        key={checkpoint.id}
        style={{
          display: "grid",
          gridTemplateColumns: "36px 1fr auto auto",
          gap: 12,
          alignItems: "center",
          padding: "10px 14px",
          borderRadius: 14,
          background: isActive
            ? "rgba(91,216,211,0.08)"
            : checkpoint.is_done
              ? "rgba(255,255,255,0.02)"
              : "rgba(255,255,255,0.04)",
          border: isActive ? "1px solid rgba(91,216,211,0.25)" : "1px solid transparent",
          opacity: checkpoint.is_done && !isActive ? 0.55 : 1,
        }}
      >
        {/* Чекбокс */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
          <input
            type="checkbox"
            checked={checkpoint.is_done}
            aria-label={`Тема ${checkpoint.title} завершена`}
            onChange={() => onToggleDone(checkpoint)}
          />
        </div>

        {/* Название + описание + прогресс */}
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
            <span
              style={{
                fontWeight: 600,
                fontSize: 14,
                textDecoration: checkpoint.is_done ? "line-through" : "none",
                opacity: checkpoint.is_done ? 0.5 : 1,
              }}
            >
              {idx}. {checkpoint.title}
            </span>
            {isActive && (
              <span className="badge acl" style={{ fontSize: 11, padding: "2px 8px" }}>
                в процессе
              </span>
            )}
          </div>
          {checkpoint.description && (
            <div className="page-sub" style={{ fontSize: 12, marginBottom: 5 }}>
              {checkpoint.description}
            </div>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 120,
                height: 5,
                borderRadius: 999,
                background: "rgba(255,255,255,0.08)",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${Math.min(100, checkpoint.progress_percent)}%`,
                  height: "100%",
                  borderRadius: 999,
                  background: checkpoint.is_done
                    ? "var(--green)"
                    : "linear-gradient(90deg, var(--blue), var(--green))",
                }}
              />
            </div>
            <span className="page-sub" style={{ fontSize: 11 }}>
              {checkpoint.progress_percent}%
            </span>
            <span className="page-sub" style={{ fontSize: 11, opacity: 0.6 }}>
              {formatDuration(spentSeconds)}
            </span>
          </div>
        </div>

        {/* Кнопки действий */}
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          {isActive ? (
            <button
              className="btn btn-secondary"
              type="button"
              disabled={isPending}
              onClick={() => onStop(checkpoint)}
              style={{ fontSize: 12, borderRadius: 20, minWidth: 64 }}
            >
              Стоп
            </button>
          ) : (
            <button
              className="btn btn-secondary"
              type="button"
              disabled={isPending || checkpoint.is_done || !!activeSession}
              onClick={() => onStart(checkpoint)}
              style={{
                fontSize: 12,
                borderRadius: 20,
                minWidth: 64,
                opacity: activeSession && !isActive ? 0.35 : 1,
              }}
              title={
                activeSession && !isActive
                  ? "Остановите текущую сессию перед запуском другой"
                  : undefined
              }
            >
              Старт
            </button>
          )}
          <button
            type="button"
            className="btn btn-secondary"
            disabled={isPending || isActive}
            aria-label={`Удалить тему ${checkpoint.title}`}
            style={{ borderRadius: 20, fontSize: 12, padding: "3px 8px", opacity: 0.4 }}
            title={isActive ? "Нельзя удалить активную тему" : "Удалить тему"}
            onClick={() => onDeleteCheckpoint(checkpoint)}
          >
            ×
          </button>
        </div>
      </div>
    );
  }

  function renderModule(mod: StudyModule) {
    const checkpoints = moduleMap.get(mod.id) ?? [];
    const doneCount = checkpoints.filter((cp) => cp.is_done).length;
    const progressPct = checkpoints.length > 0 ? Math.round((doneCount / checkpoints.length) * 100) : 0;

    return (
      <div key={mod.id} style={{ display: "grid", gap: 6 }}>
        {/* Заголовок модуля */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 14px",
            borderRadius: 12,
            background: "rgba(255,255,255,0.03)",
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 13, letterSpacing: "0.04em", textTransform: "uppercase", opacity: 0.7 }}>
                {mod.title}
              </span>
              <span className="page-sub" style={{ fontSize: 12 }}>
                {doneCount}/{checkpoints.length}
              </span>
            </div>
            {/* Прогресс-бар модуля */}
            <div
              style={{
                marginTop: 5,
                height: 3,
                borderRadius: 999,
                background: "rgba(255,255,255,0.08)",
                overflow: "hidden",
                maxWidth: 200,
              }}
            >
              <div
                style={{
                  width: `${progressPct}%`,
                  height: "100%",
                  borderRadius: 999,
                  background: progressPct === 100 ? "var(--green)" : "linear-gradient(90deg, var(--blue), var(--green))",
                }}
              />
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            disabled={isPending}
            aria-label={`Удалить модуль ${mod.title}`}
            style={{ borderRadius: 20, fontSize: 12, padding: "3px 10px", opacity: 0.45 }}
            onClick={() => onDeleteModule(mod)}
          >
            ×
          </button>
        </div>

        {/* Темы модуля */}
        {checkpoints.length > 0 ? (
          <div style={{ display: "grid", gap: 5, paddingLeft: 12 }}>
            {checkpoints.map((cp) => renderCheckpoint(cp))}
          </div>
        ) : (
          <div className="page-sub" style={{ paddingLeft: 26, fontSize: 12 }}>
            Нет тем в этом модуле
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: 16 }}>
      {orderedModules.map((mod) => renderModule(mod))}
      {unassigned.length > 0 && (
        <div style={{ display: "grid", gap: 5 }}>
          {plan.modules.length > 0 && (
            <div className="page-sub" style={{ fontSize: 12, padding: "4px 14px", opacity: 0.5 }}>
              Без модуля
            </div>
          )}
          {unassigned.map((cp) => renderCheckpoint(cp))}
        </div>
      )}
    </div>
  );
}
