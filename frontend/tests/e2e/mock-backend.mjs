import http from "node:http";
import { randomUUID } from "node:crypto";

const PORT = Number(process.env.MOCK_BACKEND_PORT ?? "8000");
const SESSION_TOKEN = "mock-session";
const CSRF_TOKEN = "mock-csrf";
const AUTH_USER = {
  id: "user-1",
  username: "shamil.isaev",
  full_name: "Шамиль Исаев",
  is_active: true,
  role: "developer",
};

const state = {
  plans: [],
  workTimerTasks: [],
  nextPlanIndex: 1,
  nextModuleIndex: 1,
  nextCheckpointIndex: 1,
  nextChecklistItemIndex: 1,
  nextSessionIndex: 1,
  nextWorkTaskIndex: 1,
  nextWorkSessionIndex: 1,
  nextWorkInterruptionIndex: 1,
};

function nowIso() {
  return new Date().toISOString();
}

function addSeconds(isoValue, seconds) {
  return new Date(new Date(isoValue).getTime() + seconds * 1000).toISOString();
}

function parseCookies(cookieHeader) {
  const cookies = {};
  if (!cookieHeader) return cookies;
  for (const chunk of cookieHeader.split(";")) {
    const [rawName, ...rawValue] = chunk.trim().split("=");
    if (!rawName) continue;
    cookies[rawName] = rawValue.join("=");
  }
  return cookies;
}

function getSessionToken(request) {
  return parseCookies(request.headers.cookie ?? "")["netops_session"] ?? null;
}

function isAuthorized(request) {
  return getSessionToken(request) === SESSION_TOKEN;
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  const raw = Buffer.concat(chunks).toString("utf-8");
  if (!raw) {
    return {};
  }
  return JSON.parse(raw);
}

function writeJson(response, statusCode, payload, headers = {}) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json",
    ...headers,
  });
  response.end(JSON.stringify(payload));
}

function writeEmpty(response, statusCode, headers = {}) {
  response.writeHead(statusCode, headers);
  response.end();
}

function createPlan({
  title,
  description = null,
  track = "python",
  status = "draft",
}) {
  const timestamp = nowIso();
  return {
    id: `plan-${state.nextPlanIndex++}`,
    user_id: AUTH_USER.id,
    title,
    description,
    track,
    status,
    total_seconds: 0,
    active_session_id: null,
    active_session_started_at: null,
    created_at: timestamp,
    updated_at: timestamp,
    modules: [],
    checkpoints: [],
    checklist_items: [],
    sessions: [],
  };
}

function createCheckpoint(plan, payload) {
  const timestamp = nowIso();
  const checkpoint = {
    id: `checkpoint-${state.nextCheckpointIndex++}`,
    plan_id: plan.id,
    module_id: payload.module_id ?? null,
    title: payload.title,
    description: payload.description ?? null,
    order_index: payload.order_index ?? plan.checkpoints.length,
    progress_percent: 0,
    is_done: false,
    completed_at: null,
    created_at: timestamp,
    updated_at: timestamp,
  };
  plan.checkpoints.push(checkpoint);
  plan.updated_at = timestamp;
  return checkpoint;
}

function createModule(plan, payload) {
  const timestamp = nowIso();
  const module = {
    id: `module-${state.nextModuleIndex++}`,
    plan_id: plan.id,
    title: payload.title,
    description: payload.description ?? null,
    order_index: payload.order_index ?? plan.modules.length,
    created_at: timestamp,
    updated_at: timestamp,
  };
  plan.modules.push(module);
  plan.updated_at = timestamp;
  return module;
}

function createChecklistItem(plan, payload) {
  const timestamp = nowIso();
  const item = {
    id: `checklist-${state.nextChecklistItemIndex++}`,
    plan_id: plan.id,
    checkpoint_id: payload.checkpoint_id ?? null,
    title: payload.title,
    description: payload.description ?? null,
    order_index: payload.order_index ?? plan.checklist_items.length,
    is_done: false,
    completed_at: null,
    created_at: timestamp,
    updated_at: timestamp,
  };
  plan.checklist_items.push(item);
  plan.updated_at = timestamp;
  return item;
}

function normalizeProgress(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return 0;
  }
  return Math.max(0, Math.min(100, Number(value)));
}

function recalculatePlan(plan) {
  plan.sessions.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
  plan.total_seconds = plan.sessions.reduce((sum, session) => sum + session.duration_seconds, 0);
  const activeSession = plan.sessions.find((session) => session.ended_at === null) ?? null;
  plan.active_session_id = activeSession ? activeSession.id : null;
  plan.active_session_started_at = activeSession ? activeSession.started_at : null;
}

function serializePlan(plan) {
  recalculatePlan(plan);
  return structuredClone(plan);
}

function getPlan(planId) {
  return state.plans.find((plan) => plan.id === planId) ?? null;
}

function getCheckpoint(checkpointId) {
  for (const plan of state.plans) {
    const checkpoint = plan.checkpoints.find((item) => item.id === checkpointId);
    if (checkpoint) {
      return { plan, checkpoint };
    }
  }
  return null;
}

function getActiveSessionForPlan(plan) {
  return plan.sessions.find((session) => session.ended_at === null) ?? null;
}

function getActiveSessionForUser() {
  for (const plan of state.plans) {
    const session = getActiveSessionForPlan(plan);
    if (session) {
      return { plan, session };
    }
  }
  return null;
}

function buildWeeklySummary(weekStartValue) {
  const parsedWeekStart = weekStartValue ? new Date(`${weekStartValue}T00:00:00.000Z`) : new Date();
  const weekStart = Number.isNaN(parsedWeekStart.getTime()) ? new Date() : parsedWeekStart;
  const dayKeys = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(weekStart);
    day.setUTCDate(day.getUTCDate() + index);
    return day.toISOString().slice(0, 10);
  });
  const dayTotals = Object.fromEntries(
    dayKeys.map((day) => [day, { total_seconds: 0, sessions_count: 0 }]),
  );
  const planTotals = new Map();
  const sessions = [];
  const completedCheckpoints = [];
  const weekEnd = new Date(weekStart);
  weekEnd.setUTCDate(weekEnd.getUTCDate() + 6);
  const weekEndExclusive = new Date(weekEnd);
  weekEndExclusive.setUTCDate(weekEndExclusive.getUTCDate() + 1);

  for (const plan of state.plans) {
    let totalSeconds = 0;
    let sessionsCount = 0;
    for (const session of plan.sessions) {
      const sessionEnd = session.ended_at ? new Date(session.ended_at) : new Date();
      const sessionStart = new Date(session.started_at);
      if (sessionEnd < weekStart || sessionStart >= weekEndExclusive) {
        continue;
      }

      const clippedStart = new Date(Math.max(sessionStart.getTime(), weekStart.getTime()));
      const clippedEnd = new Date(Math.min(sessionEnd.getTime(), weekEndExclusive.getTime()));
      if (clippedEnd <= clippedStart) {
        continue;
      }

      const durationSeconds = session.duration_seconds;
      totalSeconds += durationSeconds;
      sessionsCount += 1;
      sessions.push(structuredClone(session));

      const dayKey = clippedStart.toISOString().slice(0, 10);
      if (dayTotals[dayKey]) {
        dayTotals[dayKey].total_seconds += durationSeconds;
        dayTotals[dayKey].sessions_count += 1;
      }
    }

    planTotals.set(plan.id, {
      plan_id: plan.id,
      title: plan.title,
      total_seconds: totalSeconds,
      sessions_count: sessionsCount,
    });

    for (const checkpoint of plan.checkpoints) {
      if (checkpoint.completed_at) {
        const completedAt = new Date(checkpoint.completed_at);
        if (completedAt >= weekStart && completedAt < weekEndExclusive) {
          completedCheckpoints.push({
            checkpoint_id: checkpoint.id,
            plan_id: plan.id,
            plan_title: plan.title,
            title: checkpoint.title,
            completed_at: checkpoint.completed_at,
          });
        }
      }
    }
  }

  return {
    week_start: weekStart.toISOString().slice(0, 10),
    week_end: weekEnd.toISOString().slice(0, 10),
    total_seconds: Object.values(dayTotals).reduce((sum, day) => sum + day.total_seconds, 0),
    days: dayKeys.map((day) => ({ day, ...dayTotals[day] })),
    plans: [...planTotals.values()].sort((a, b) => b.total_seconds - a.total_seconds),
    sessions: sessions.sort((a, b) => new Date(b.started_at) - new Date(a.started_at)),
    completed_checkpoints: completedCheckpoints.sort(
      (a, b) => new Date(b.completed_at) - new Date(a.completed_at),
    ),
  };
}

function buildPlanResponse(plan) {
  return serializePlan(plan);
}

function normalizeTags(tags = []) {
  const normalized = [];
  for (const tag of tags) {
    const clean = String(tag).trim();
    if (clean && !normalized.includes(clean)) {
      normalized.push(clean);
    }
  }
  return normalized;
}

function createWorkTask(payload) {
  const timestamp = nowIso();
  return {
    id: `work-task-${state.nextWorkTaskIndex++}`,
    user_id: AUTH_USER.id,
    title: String(payload.title ?? "").trim() || "Новая задача",
    description: payload.description ?? null,
    task_ref: payload.task_ref ?? null,
    task_url: payload.task_url ?? null,
    tags: normalizeTags(payload.tags ?? []),
    order_index: Number(payload.order_index ?? 0),
    status: payload.status ?? "todo",
    completed_at: null,
    created_at: timestamp,
    updated_at: timestamp,
    sessions: [],
  };
}

function workTaskDuration(session) {
  const startedAt = new Date(session.started_at);
  const endedAt = session.ended_at ? new Date(session.ended_at) : new Date();
  const interruptionSeconds = (session.interruptions ?? []).reduce((sum, interruption) => {
    const interruptionEnd = interruption.ended_at ? new Date(interruption.ended_at) : new Date();
    return sum + Math.max(0, Math.floor((interruptionEnd - new Date(interruption.started_at)) / 1000));
  }, 0);
  return Math.max(0, Math.floor((endedAt - startedAt) / 1000) - interruptionSeconds);
}

function recalculateWorkTask(task) {
  task.sessions.sort((a, b) => new Date(a.started_at) - new Date(b.started_at));
  task.total_seconds = task.sessions.reduce((sum, session) => sum + workTaskDuration(session), 0);
  task.interruption_seconds = task.sessions.reduce(
    (sum, session) =>
      sum +
      (session.interruptions ?? []).reduce((inner, interruption) => {
        const interruptionEnd = interruption.ended_at ? new Date(interruption.ended_at) : new Date();
        return inner + Math.max(0, Math.floor((interruptionEnd - new Date(interruption.started_at)) / 1000));
      }, 0),
    0,
  );
  task.interruptions_count = task.sessions.reduce((sum, session) => sum + (session.interruptions ?? []).length, 0);
  const activeSession = task.sessions.find((session) => session.ended_at === null) ?? null;
  task.active_session_id = activeSession ? activeSession.id : null;
  task.active_session_started_at = activeSession ? activeSession.started_at : null;
}

function buildWorkTaskResponse(task) {
  recalculateWorkTask(task);
  return structuredClone(task);
}

function getWorkTask(taskId) {
  return state.workTimerTasks.find((task) => task.id === taskId) ?? null;
}

function getWorkActiveSessionForTask(task) {
  return task.sessions.find((session) => session.ended_at === null) ?? null;
}

function getWorkActiveSessionForUser() {
  for (const task of state.workTimerTasks) {
    const session = getWorkActiveSessionForTask(task);
    if (session) {
      return { task, session };
    }
  }
  return null;
}

function buildWorkWeeklySummary(weekStartValue) {
  const parsedWeekStart = weekStartValue ? new Date(`${weekStartValue}T00:00:00.000Z`) : new Date();
  const weekStart = Number.isNaN(parsedWeekStart.getTime()) ? new Date() : parsedWeekStart;
  const dayKeys = Array.from({ length: 7 }, (_, index) => {
    const day = new Date(weekStart);
    day.setUTCDate(day.getUTCDate() + index);
    return day.toISOString().slice(0, 10);
  });
  const dayTotals = Object.fromEntries(
    dayKeys.map((day) => [day, { total_seconds: 0, sessions_count: 0, interruptions_count: 0 }]),
  );
  const taskTotals = new Map();
  const tagTotals = new Map();
  const sessions = [];
  const weekEndExclusive = new Date(weekStart);
  weekEndExclusive.setUTCDate(weekEndExclusive.getUTCDate() + 7);

  for (const task of state.workTimerTasks) {
    for (const session of task.sessions) {
      const sessionStart = new Date(session.started_at);
      if (sessionStart < weekStart || sessionStart >= weekEndExclusive) {
        continue;
      }

      const durationSeconds = workTaskDuration(session);
      const interruptionSeconds = (session.interruptions ?? []).reduce((sum, interruption) => {
        const interruptionEnd = interruption.ended_at ? new Date(interruption.ended_at) : new Date();
        return sum + Math.max(0, Math.floor((interruptionEnd - new Date(interruption.started_at)) / 1000));
      }, 0);

      sessions.push(structuredClone(session));
      const dayKey = sessionStart.toISOString().slice(0, 10);
      if (dayTotals[dayKey]) {
        dayTotals[dayKey].total_seconds += durationSeconds;
        dayTotals[dayKey].sessions_count += 1;
        dayTotals[dayKey].interruptions_count += session.interruptions?.length ?? 0;
      }

      const taskBucket = taskTotals.get(task.id) ?? {
        task_id: task.id,
        title: task.title,
        total_seconds: 0,
        sessions_count: 0,
        interruptions_count: 0,
        tags: [...(session.tags_snapshot ?? [])],
      };
      taskBucket.total_seconds += durationSeconds;
      taskBucket.sessions_count += 1;
      taskBucket.interruptions_count += session.interruptions?.length ?? 0;
      taskBucket.tags = [...(session.tags_snapshot ?? [])];
      taskTotals.set(task.id, taskBucket);

      for (const tag of session.tags_snapshot ?? []) {
        const tagBucket = tagTotals.get(tag) ?? {
          tag,
          total_seconds: 0,
          sessions_count: 0,
        };
        tagBucket.total_seconds += durationSeconds;
        tagBucket.sessions_count += 1;
        tagTotals.set(tag, tagBucket);
      }
    }
  }

  return {
    week_start: weekStart.toISOString().slice(0, 10),
    week_end: new Date(weekEndExclusive.getTime() - 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10),
    total_seconds: Object.values(dayTotals).reduce((sum, day) => sum + day.total_seconds, 0),
    days: dayKeys.map((day) => ({ day, ...dayTotals[day] })),
    tasks: [...taskTotals.values()].sort((a, b) => b.total_seconds - a.total_seconds),
    tags: [...tagTotals.values()].sort((a, b) => b.total_seconds - a.total_seconds),
    sessions: sessions.sort((a, b) => new Date(b.started_at) - new Date(a.started_at)),
  };
}

function handleWorkTimer(task, payload) {
  const now = nowIso();
  if (payload.action === "start") {
    const active = getWorkActiveSessionForUser();
    if (active && active.task.id !== task.id) {
      return [400, { detail: "Сначала останови текущий активный таймер" }];
    }
    if (task.status === "done" || task.status === "cancelled") {
      return [400, { detail: "Нельзя запускать таймер для завершённой или отменённой задачи" }];
    }
    const activeSession = getWorkActiveSessionForTask(task);
    if (activeSession && activeSession.status === "paused") {
      activeSession.status = "running";
      activeSession.ended_at = null;
      activeSession.updated_at = now;
      const interruption = activeSession.interruptions.find((item) => item.ended_at === null);
      if (interruption) {
        interruption.ended_at = now;
        interruption.updated_at = now;
      }
      task.status = "in_progress";
      task.updated_at = now;
      return [200, buildWorkTaskResponse(task)];
    }
    if (activeSession && activeSession.status === "running") {
      return [200, buildWorkTaskResponse(task)];
    }
    const session = {
      id: `work-session-${state.nextWorkSessionIndex++}`,
      task_id: task.id,
      status: "running",
      tags_snapshot: [...(task.tags ?? [])],
      started_at: now,
      ended_at: null,
      created_at: now,
      updated_at: now,
      interruptions: [],
    };
    task.sessions.push(session);
    task.status = "in_progress";
    task.updated_at = now;
    return [200, buildWorkTaskResponse(task)];
  }

  const activeSession = getWorkActiveSessionForTask(task);
  if (!activeSession) {
    return [400, { detail: "Сначала запусти таймер" }];
  }

  if (payload.action === "pause") {
    if (activeSession.status !== "running") {
      return [400, { detail: "Сначала запусти таймер" }];
    }
    activeSession.status = "paused";
    activeSession.updated_at = now;
    activeSession.interruptions.push({
      id: `work-interruption-${state.nextWorkInterruptionIndex++}`,
      session_id: activeSession.id,
      reason: payload.interruption_reason ?? null,
      started_at: now,
      ended_at: null,
      created_at: now,
      updated_at: now,
    });
    task.updated_at = now;
    return [200, buildWorkTaskResponse(task)];
  }

  if (payload.action === "resume") {
    if (activeSession.status !== "paused") {
      return [400, { detail: "Сначала поставь таймер на паузу" }];
    }
    activeSession.status = "running";
    activeSession.updated_at = now;
    const interruption = activeSession.interruptions.find((item) => item.ended_at === null);
    if (interruption) {
      interruption.ended_at = now;
      interruption.updated_at = now;
    }
    task.updated_at = now;
    return [200, buildWorkTaskResponse(task)];
  }

  if (payload.action === "stop") {
    if (activeSession.status === "paused") {
      const interruption = activeSession.interruptions.find((item) => item.ended_at === null);
      if (interruption) {
        interruption.ended_at = now;
        interruption.updated_at = now;
      }
    }
    activeSession.status = "stopped";
    activeSession.ended_at = now;
    activeSession.updated_at = now;
    task.updated_at = now;
    return [200, buildWorkTaskResponse(task)];
  }

  return [400, { detail: "Неизвестное действие таймера" }];
}

function handleTimer(plan, payload) {
  const now = nowIso();
  if (payload.action === "start") {
    if (!payload.checkpoint_id) {
      return [400, { detail: "Для старта таймера нужно выбрать тему" }];
    }
    const checkpoint = plan.checkpoints.find((item) => item.id === payload.checkpoint_id);
    if (!checkpoint) {
      return [404, { detail: "Тема не найдена в выбранном учебном плане" }];
    }
    if (checkpoint.is_done) {
      return [400, { detail: "Эта тема уже закрыта" }];
    }
    if (getActiveSessionForUser()) {
      return [400, { detail: "Сначала останови активный таймер у другого учебного плана" }];
    }

    plan.status = "active";
    const session = {
      id: `session-${state.nextSessionIndex++}`,
      plan_id: plan.id,
      checkpoint_id: checkpoint.id,
      status: "running",
      progress_percent: 0,
      started_at: now,
      ended_at: null,
      duration_seconds: 0,
      created_at: now,
      updated_at: now,
    };
    plan.sessions.push(session);
    plan.updated_at = now;
    return [200, buildPlanResponse(plan)];
  }

  const activeSession = getActiveSessionForPlan(plan);
  if (!activeSession) {
    return [400, { detail: "Для этого учебного плана нет активного таймера" }];
  }
  const checkpoint = plan.checkpoints.find((item) => item.id === activeSession.checkpoint_id);
  if (!checkpoint) {
    return [404, { detail: "Тема не найдена в выбранном учебном плане" }];
  }

  if (payload.action === "pause") {
    activeSession.status = "paused";
    activeSession.ended_at = now;
    activeSession.duration_seconds = 60;
  } else if (payload.action === "stop") {
    const progress = normalizeProgress(payload.progress_percent);
    activeSession.status = "stopped";
    activeSession.progress_percent = progress;
    activeSession.ended_at = now;
    activeSession.duration_seconds = 60;
    checkpoint.progress_percent = Math.max(checkpoint.progress_percent, progress);
    if (checkpoint.progress_percent >= 100) {
      checkpoint.is_done = true;
      checkpoint.completed_at = now;
    }
    checkpoint.updated_at = now;
  } else {
    return [400, { detail: "Неизвестное действие таймера" }];
  }

  activeSession.updated_at = now;
  plan.updated_at = now;
  return [200, buildPlanResponse(plan)];
}

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", "http://127.0.0.1");
  const { pathname, searchParams } = url;
  const method = request.method ?? "GET";

  if (method === "GET" && pathname === "/api/v1/health") {
    return writeJson(response, 200, {
      status: "ok",
      app: "netops-assistant-mock-backend",
      environment: "e2e",
      timestamp: nowIso(),
    });
  }

  if (method === "POST" && pathname === "/__reset") {
    state.plans = [];
    state.workTimerTasks = [];
    state.nextPlanIndex = 1;
    state.nextModuleIndex = 1;
    state.nextCheckpointIndex = 1;
    state.nextChecklistItemIndex = 1;
    state.nextSessionIndex = 1;
    state.nextWorkTaskIndex = 1;
    state.nextWorkSessionIndex = 1;
    state.nextWorkInterruptionIndex = 1;
    return writeEmpty(response, 204);
  }

  if (method === "POST" && pathname === "/api/v1/auth/login") {
    const payload = await readJson(request);
    const username = String(payload.username ?? "");
    const password = String(payload.password ?? "");
    if (username !== "shamil.isaev" || password !== "12345678") {
      return writeJson(response, 401, { detail: "Ошибка входа" });
    }
    return writeJson(
      response,
      200,
      { message: "ok", user: AUTH_USER },
      {
        "Set-Cookie": [
          `netops_session=${SESSION_TOKEN}; Path=/; HttpOnly; SameSite=Lax`,
          `netops_csrf=${CSRF_TOKEN}; Path=/; SameSite=Lax`,
        ],
      },
    );
  }

  if (method === "GET" && pathname === "/api/v1/auth/me") {
    if (!isAuthorized(request)) {
      return writeJson(response, 401, { detail: "Не авторизован" });
    }
    return writeJson(response, 200, AUTH_USER);
  }

  if (method === "POST" && pathname === "/api/v1/auth/logout") {
    return writeEmpty(response, 204);
  }

  if (!isAuthorized(request)) {
    return writeJson(response, 401, { detail: "Не авторизован" });
  }

  if (method === "GET" && pathname === "/api/v1/study/plans") {
    return writeJson(response, 200, state.plans.map(buildPlanResponse));
  }

  if (method === "GET" && pathname === "/api/v1/work-timer/tasks") {
    return writeJson(response, 200, state.workTimerTasks.map(buildWorkTaskResponse));
  }

  if (method === "POST" && pathname === "/api/v1/work-timer/tasks") {
    const payload = await readJson(request);
    const task = createWorkTask(payload);
    state.workTimerTasks.unshift(task);
    return writeJson(response, 201, buildWorkTaskResponse(task));
  }

  if (method === "PATCH" && pathname.startsWith("/api/v1/work-timer/tasks/")) {
    const taskId = pathname.split("/")[5];
    const task = getWorkTask(taskId);
    if (!task) {
      return writeJson(response, 404, { detail: "Задача не найдена" });
    }
    const payload = await readJson(request);
    if (typeof payload.title === "string") {
      task.title = payload.title.trim() || task.title;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "description")) {
      task.description = payload.description ?? null;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "task_ref")) {
      task.task_ref = payload.task_ref ?? null;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "task_url")) {
      task.task_url = payload.task_url ?? null;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "tags") && payload.tags !== null) {
      task.tags = normalizeTags(payload.tags ?? []);
    }
    if (Object.prototype.hasOwnProperty.call(payload, "order_index") && payload.order_index !== null) {
      task.order_index = Number(payload.order_index);
    }
    if (Object.prototype.hasOwnProperty.call(payload, "status") && payload.status !== null) {
      task.status = payload.status;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "completed_at")) {
      task.completed_at = payload.completed_at ?? null;
    }
    task.updated_at = nowIso();
    return writeJson(response, 200, buildWorkTaskResponse(task));
  }

  if (method === "DELETE" && pathname.startsWith("/api/v1/work-timer/tasks/")) {
    const taskId = pathname.split("/")[5];
    state.workTimerTasks = state.workTimerTasks.filter((task) => task.id !== taskId);
    return writeEmpty(response, 204);
  }

  if (method === "POST" && pathname.match(/^\/api\/v1\/work-timer\/tasks\/[^/]+\/timer$/)) {
    const taskId = pathname.split("/")[5];
    const task = getWorkTask(taskId);
    if (!task) {
      return writeJson(response, 404, { detail: "Задача не найдена" });
    }
    const payload = await readJson(request);
    const [status, body] = handleWorkTimer(task, payload);
    return writeJson(response, status, body);
  }

  if (method === "POST" && pathname === "/api/v1/study/plans") {
    const payload = await readJson(request);
    const plan = createPlan({
      title: String(payload.title ?? "").trim() || "Новый план",
      description: payload.description ?? null,
      track: payload.track ?? "python",
      status: payload.status ?? "draft",
    });
    state.plans.unshift(plan);
    return writeJson(response, 201, buildPlanResponse(plan));
  }

  if (method === "PATCH" && pathname.startsWith("/api/v1/study/plans/")) {
    const [, , , , , planId] = pathname.split("/");
    const plan = getPlan(planId);
    if (!plan) {
      return writeJson(response, 404, { detail: "План не найден" });
    }
    const payload = await readJson(request);
    if (typeof payload.title === "string") {
      plan.title = payload.title.trim() || plan.title;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "description")) {
      plan.description = payload.description ?? null;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "track") && payload.track !== null) {
      plan.track = payload.track;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "status") && payload.status !== null) {
      plan.status = payload.status;
    }
    plan.updated_at = nowIso();
    return writeJson(response, 200, buildPlanResponse(plan));
  }

  if (method === "DELETE" && pathname.startsWith("/api/v1/study/plans/")) {
    const [, , , , , planId] = pathname.split("/");
    state.plans = state.plans.filter((plan) => plan.id !== planId);
    return writeEmpty(response, 204);
  }

  if (method === "POST" && pathname.match(/^\/api\/v1\/study\/plans\/[^/]+\/checkpoints$/)) {
    const planId = pathname.split("/")[5];
    const plan = getPlan(planId);
    if (!plan) {
      return writeJson(response, 404, { detail: "План не найден" });
    }
    const payload = await readJson(request);
    createCheckpoint(plan, payload);
    return writeJson(response, 201, buildPlanResponse(plan));
  }

  if (
    method === "POST" &&
    pathname.match(/^\/api\/v1\/study\/plans\/[^/]+\/checkpoints\/bulk$/)
  ) {
    const planId = pathname.split("/")[5];
    const plan = getPlan(planId);
    if (!plan) {
      return writeJson(response, 404, { detail: "План не найден" });
    }
    const payload = await readJson(request);
    for (const section of payload.sections ?? []) {
      const moduleId = section.module_title ? createModule(plan, {
        title: section.module_title,
        description: null,
        order_index: plan.modules.length,
      }).id : null;
      for (const topic of section.topics ?? []) {
        createCheckpoint(plan, {
          title: topic,
          description: null,
          module_id: moduleId,
          order_index: plan.checkpoints.length,
        });
      }
    }
    return writeJson(response, 201, buildPlanResponse(plan));
  }

  if (method === "POST" && pathname.match(/^\/api\/v1\/study\/plans\/[^/]+\/modules$/)) {
    const planId = pathname.split("/")[5];
    const plan = getPlan(planId);
    if (!plan) {
      return writeJson(response, 404, { detail: "План не найден" });
    }
    const payload = await readJson(request);
    createModule(plan, payload);
    return writeJson(response, 201, buildPlanResponse(plan));
  }

  if (method === "POST" && pathname.match(/^\/api\/v1\/study\/plans\/[^/]+\/checklist-items$/)) {
    const planId = pathname.split("/")[5];
    const plan = getPlan(planId);
    if (!plan) {
      return writeJson(response, 404, { detail: "План не найден" });
    }
    const payload = await readJson(request);
    createChecklistItem(plan, payload);
    return writeJson(response, 201, buildPlanResponse(plan));
  }

  if (method === "POST" && pathname.match(/^\/api\/v1\/study\/plans\/[^/]+\/timer$/)) {
    const planId = pathname.split("/")[5];
    const plan = getPlan(planId);
    if (!plan) {
      return writeJson(response, 404, { detail: "План не найден" });
    }
    const payload = await readJson(request);
    const [status, body] = handleTimer(plan, payload);
    return writeJson(response, status, body);
  }

  if (method === "PATCH" && pathname.startsWith("/api/v1/study/checkpoints/")) {
    const checkpointId = pathname.split("/")[5];
    const result = getCheckpoint(checkpointId);
    if (!result) {
      return writeJson(response, 404, { detail: "Тема не найдена" });
    }
    const { plan, checkpoint } = result;
    const payload = await readJson(request);
    if (typeof payload.title === "string") {
      checkpoint.title = payload.title.trim() || checkpoint.title;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "description")) {
      checkpoint.description = payload.description ?? null;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "order_index") && payload.order_index !== null) {
      checkpoint.order_index = payload.order_index;
    }
    if (Object.prototype.hasOwnProperty.call(payload, "is_done") && payload.is_done !== null) {
      checkpoint.is_done = Boolean(payload.is_done);
      if (checkpoint.is_done) {
        checkpoint.completed_at = nowIso();
        checkpoint.progress_percent = 100;
      }
    }
    checkpoint.updated_at = nowIso();
    plan.updated_at = checkpoint.updated_at;
    return writeJson(response, 200, buildPlanResponse(plan));
  }

  if (method === "DELETE" && pathname.startsWith("/api/v1/study/checkpoints/")) {
    const checkpointId = pathname.split("/")[5];
    const result = getCheckpoint(checkpointId);
    if (!result) {
      return writeEmpty(response, 204);
    }
    result.plan.checkpoints = result.plan.checkpoints.filter((item) => item.id !== checkpointId);
    result.plan.updated_at = nowIso();
    return writeEmpty(response, 204);
  }

  if (method === "DELETE" && pathname.startsWith("/api/v1/study/modules/")) {
    const moduleId = pathname.split("/")[5];
    for (const plan of state.plans) {
      plan.modules = plan.modules.filter((item) => item.id !== moduleId);
      plan.checkpoints.forEach((checkpoint) => {
        if (checkpoint.module_id === moduleId) {
          checkpoint.module_id = null;
        }
      });
    }
    return writeEmpty(response, 204);
  }

  if (method === "GET" && pathname === "/api/v1/study/weekly-summary") {
    return writeJson(response, 200, buildWeeklySummary(searchParams.get("week_start") ?? ""));
  }

  if (method === "GET" && pathname === "/api/v1/work-timer/weekly-summary") {
    return writeJson(
      response,
      200,
      buildWorkWeeklySummary(searchParams.get("week_start") ?? ""),
    );
  }

  return writeJson(response, 404, { detail: `Not found: ${method} ${pathname}` });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`[mock-backend] listening on http://127.0.0.1:${PORT}`);
});
