import { cookies } from "next/headers";

import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";
import { SERVER_API_BASE_URL } from "@/lib/api-url";

export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  timestamp: string;
};

export type DashboardActivityCounters = {
  total: number;
  call: number;
  ticket: number;
  meeting: number;
  task: number;
  escalation: number;
  other: number;
};

export type DashboardStatusCounters = {
  open: number;
  in_progress: number;
  closed: number;
  cancelled: number;
};

export type CurrentUser = {
  id: string;
  username: string;
  full_name: string;
  is_active: boolean;
  role: string;
};

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginResponse = {
  message: string;
  user: CurrentUser;
};

export type ActivityEntry = {
  id: string;
  user_id: string;
  work_date: string;
  activity_type: string;
  status: string;
  title: string;
  description: string | null;
  resolution: string | null;
  contact: string | null;
  service: string | null;
  ticket_number: string | null;
  task_url: string | null;
  started_at: string | null;
  ended_at: string | null;
  is_backdated: boolean;
  created_at: string;
  updated_at: string;
};

export type ArchiveResponse = {
  total: number;
  limit: number;
  offset: number;
  results: ActivityEntry[];
};

export type ArchiveQueryParams = {
  q?: string;
  activity_type?: string;
  external_ref?: string;
  service?: string;
  ticket_number?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
};

export type ReportRecord = {
  id: string;
  report_type: string;
  report_status: string;
  period_from: string;
  period_to: string;
  generated_at: string;
};

export type ReportPreview = {
  report_id: string;
  report_type: string;
  report_status: string;
  period_from: string;
  period_to: string;
  content_md: string;
  generated_at: string;
  updates_after_finalization: number;
};

export type GenerateReportPayload =
  | {
      report_type: "daily";
      report_date: string;
      format_profile?: "engineer" | "manager";
      service_filter_mode?: "all" | "include" | "exclude" | "empty";
      service_filters?: string[];
    }
  | {
      report_type: "weekly";
      week_start: string;
      format_profile?: "engineer" | "manager";
      service_filter_mode?: "all" | "include" | "exclude" | "empty";
      service_filters?: string[];
    }
  | {
      report_type: "range";
      date_from: string;
      date_to: string;
      format_profile?: "engineer" | "manager";
      service_filter_mode?: "all" | "include" | "exclude" | "empty";
      service_filters?: string[];
    }
  | { report_type: "night_work_result"; plan_id: string; format_profile?: "engineer" | "manager" };

export type NightWorkStep = {
  id: string;
  block_id: string;
  title: string;
  description: string | null;
  status: string;
  order_index: number;
  is_rollback: boolean;
  is_post_action: boolean;
  actual_result: string | null;
  executor_comment: string | null;
  collaborators: string[];
  handoff_to: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
};

export type NightWorkBlock = {
  id: string;
  plan_id: string;
  sr_number: string | null;
  title: string;
  description: string | null;
  status: string;
  order_index: number;
  started_at: string | null;
  finished_at: string | null;
  result_comment: string | null;
  created_at: string;
  steps: NightWorkStep[];
};

export type NightWorkPlan = {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  status: string;
  scheduled_at: string | null;
  participants: string[];
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
  blocks: NightWorkBlock[];
};

export type StudyPlanStatus = "draft" | "active" | "completed" | "cancelled";
export type StudySessionStatus = "running" | "paused" | "stopped";
export type StudyPlanTrack = "python" | "networks";

export type StudyModule = {
  id: string;
  plan_id: string;
  title: string;
  description: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
};

export type StudyCheckpoint = {
  id: string;
  plan_id: string;
  module_id: string | null;
  title: string;
  description: string | null;
  order_index: number;
  progress_percent: number;
  is_done: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type StudyChecklistItem = {
  id: string;
  plan_id: string;
  checkpoint_id: string | null;
  title: string;
  description: string | null;
  order_index: number;
  is_done: boolean;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type StudySession = {
  id: string;
  plan_id: string;
  checkpoint_id: string | null;
  status: StudySessionStatus;
  progress_percent: number;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number;
  created_at: string;
  updated_at: string;
};

export type StudyPlan = {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  track: StudyPlanTrack;
  status: StudyPlanStatus;
  total_seconds: number;
  active_session_id: string | null;
  active_session_started_at: string | null;
  created_at: string;
  updated_at: string;
  modules: StudyModule[];
  checkpoints: StudyCheckpoint[];
  checklist_items: StudyChecklistItem[];
  sessions: StudySession[];
};

export type StudyWeeklyDaySummary = {
  day: string;
  total_seconds: number;
  sessions_count: number;
};

export type StudyWeeklyPlanSummary = {
  plan_id: string;
  title: string;
  total_seconds: number;
  sessions_count: number;
};

export type StudyCheckpointCompletionSummary = {
  checkpoint_id: string;
  plan_id: string;
  plan_title: string;
  title: string;
  completed_at: string;
};

export type StudyWeeklySummary = {
  week_start: string;
  week_end: string;
  total_seconds: number;
  days: StudyWeeklyDaySummary[];
  plans: StudyWeeklyPlanSummary[];
  sessions: StudySession[];
  completed_checkpoints: StudyCheckpointCompletionSummary[];
};

export type PlanTemplate = {
  id: string;
  user_id: string;
  key: string;
  name: string;
  category: string;
  description: string | null;
  template_payload: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TeamMember = {
  id: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  teams: string[];
};

export type LocalUser = {
  id: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

export type TeamWeeklySummary = {
  user_id: string;
  username: string;
  full_name: string;
  total_entries: number;
  by_status: Record<string, number>;
  by_activity_type: Record<string, number>;
};

export type JournalActivityType = "call" | "ticket" | "meeting" | "task" | "escalation" | "other";
export type JournalActivityStatus = "open" | "in_progress" | "closed" | "cancelled";

export type JournalEntry = {
  id: string;
  user_id: string;
  work_date: string;
  activity_type: JournalActivityType;
  status: JournalActivityStatus;
  title: string;
  description: string | null;
  resolution: string | null;
  contact: string | null;
  service: string | null;
  ticket_number: string | null;
  task_url: string | null;
  started_at: string | null;
  ended_at: string | null;
  ended_date: string | null;
  is_backdated: boolean;
  created_at: string;
  updated_at: string;
};

export type PlannedEvent = {
  id: string;
  user_id: string;
  event_type: string;
  title: string;
  description: string | null;
  external_ref: string | null;
  scheduled_at: string;
  is_completed: boolean;
  linked_journal_entry_id: string | null;
  created_at: string;
  updated_at: string;
};

export type DayDashboardResponse = {
  date: string;
  generated_at: string;
  activity_counters: DashboardActivityCounters;
  status_counters: DashboardStatusCounters;
  timeline: JournalEntry[];
  planned_today: PlannedEvent[];
};

export type JournalEntriesResponse = {
  work_date: string;
  total: number;
  items: JournalEntry[];
};

export type JournalDeduplicationResponse = {
  work_date: string;
  removed: number;
  duplicate_ticket_numbers: string[];
};

export type JournalBulkDeleteResponse = {
  scope: "work_date" | "all" | "selected";
  removed: number;
  work_date: string | null;
};

export type JournalSelectedDeletePayload = {
  entry_ids: string[];
};

export type CreateJournalEntryPayload = {
  work_date: string;
  activity_type: JournalActivityType;
  status?: JournalActivityStatus;
  title: string;
  description?: string | null;
  resolution?: string | null;
  contact?: string | null;
  service?: string | null;
  ticket_number?: string | null;
  task_url?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
  ended_date?: string | null;
};

export type BulkJournalImportPayload = {
  text: string;
  default_work_date?: string;
};

export type BulkJournalImportResponse = {
  created: number;
  items: JournalEntry[];
  warnings: string[];
};

export type BulkJournalImportPreviewItem = {
  work_date: string;
  activity_type: JournalActivityType;
  status: JournalActivityStatus;
  title: string;
  service: string | null;
  ticket_number: string | null;
  task_url: string | null;
};

export type BulkJournalImportPreviewResponse = {
  total: number;
  items: BulkJournalImportPreviewItem[];
  warnings: string[];
};

export type DashboardDatePoint = {
  date: string;
  total: number;
};

export type DashboardWeekPoint = {
  week_start: string;
  week_end: string;
  total: number;
};

export type DashboardServicePoint = {
  service: string;
  total: number;
  share: number;
};

export type DashboardAnalyticsResponse = {
  generated_at: string;
  period_start: string;
  period_end: string;
  today_total: number;
  week_total: number;
  total_entries: number;
  daily_series: DashboardDatePoint[];
  weekly_series: DashboardWeekPoint[];
  service_breakdown: DashboardServicePoint[];
};

// Все функции в этом файле работают только на серверной стороне приложения.
// Поэтому здесь используем внутренний адрес backend, а не публичный URL из браузера.
const API_BASE_URL = SERVER_API_BASE_URL;

export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export async function getDayDashboard(workDate: string): Promise<DayDashboardResponse | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/day?work_date=${workDate}`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DayDashboardResponse;
  } catch {
    return null;
  }
}

export async function getDashboardAnalytics(): Promise<DashboardAnalyticsResponse | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/analytics`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DashboardAnalyticsResponse;
  } catch {
    return null;
  }
}

export async function loginWithBackend(payload: LoginPayload): Promise<Response> {
  return fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}

export async function logoutWithBackend(sessionToken: string, csrfToken: string | null): Promise<void> {
  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }
  await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;

  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as CurrentUser;
  } catch {
    return null;
  }
}

export async function getArchiveEntries(params: ArchiveQueryParams): Promise<ArchiveResponse | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  const searchParams = new URLSearchParams();
  if (params.q) searchParams.set("q", params.q);
  if (params.activity_type) searchParams.set("activity_type", params.activity_type);
  if (params.external_ref) searchParams.set("external_ref", params.external_ref);
  if (params.service) searchParams.set("service", params.service);
  if (params.ticket_number) searchParams.set("ticket_number", params.ticket_number);
  if (params.date_from) searchParams.set("date_from", params.date_from);
  if (params.date_to) searchParams.set("date_to", params.date_to);
  if (typeof params.limit === "number") searchParams.set("limit", String(params.limit));
  if (typeof params.offset === "number") searchParams.set("offset", String(params.offset));

  const queryString = searchParams.toString();
  const url = `${API_BASE_URL}/api/v1/search/archive${queryString ? `?${queryString}` : ""}`;

  try {
    const response = await fetch(url, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as ArchiveResponse;
  } catch {
    return null;
  }
}

export async function getReportHistory(): Promise<ReportRecord[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/reports/history`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as ReportRecord[];
  } catch {
    return null;
  }
}

export async function getReportPreview(reportId: string): Promise<ReportPreview | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/reports/${reportId}`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as ReportPreview;
  } catch {
    return null;
  }
}

export async function refreshReportWithBackend(reportId: string): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/reports/${reportId}/refresh`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function finalizeReportWithBackend(reportId: string): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/reports/${reportId}/finalize`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function regenerateDraftReportWithBackend(reportId: string): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/reports/${reportId}/regenerate-draft`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function generateReportWithBackend(payload: GenerateReportPayload): Promise<Response> {
  let path = "/api/v1/reports/daily";
  let requestBody: Record<string, string | string[]> = {};

  if (payload.report_type === "daily") {
    path = "/api/v1/reports/daily";
    requestBody = {
      report_date: payload.report_date,
      format_profile: payload.format_profile ?? "engineer",
      service_filter_mode: payload.service_filter_mode ?? "all",
      service_filters: payload.service_filters ?? [],
    };
  } else if (payload.report_type === "weekly") {
    path = "/api/v1/reports/weekly";
    requestBody = {
      week_start: payload.week_start,
      format_profile: payload.format_profile ?? "engineer",
      service_filter_mode: payload.service_filter_mode ?? "all",
      service_filters: payload.service_filters ?? [],
    };
  } else if (payload.report_type === "range") {
    path = "/api/v1/reports/range";
    requestBody = {
      date_from: payload.date_from,
      date_to: payload.date_to,
      format_profile: payload.format_profile ?? "engineer",
      service_filter_mode: payload.service_filter_mode ?? "all",
      service_filters: payload.service_filters ?? [],
    };
  } else {
    const formatProfile = payload.format_profile ?? "engineer";
    path = `/api/v1/reports/night-work/${payload.plan_id}?format_profile=${formatProfile}`;
    requestBody = {};
  }

  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(requestBody),
    cache: "no-store",
  });
}

export async function getNightWorkPlans(): Promise<NightWorkPlan[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/plans`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as NightWorkPlan[];
  } catch {
    return null;
  }
}

export async function getStudyPlans(): Promise<StudyPlan[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/study/plans`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as StudyPlan[];
  } catch {
    return null;
  }
}

export async function getStudyWeeklySummary(weekStart: string): Promise<StudyWeeklySummary | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  const query = weekStart ? `?week_start=${weekStart}` : "";
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/study/weekly-summary${query}`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as StudyWeeklySummary;
  } catch {
    return null;
  }
}

export async function getPlanTemplates(): Promise<PlanTemplate[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/templates`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as PlanTemplate[];
  } catch {
    return null;
  }
}

export async function getMyTeamMembers(): Promise<TeamMember[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/team/users/my-team`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as TeamMember[];
  } catch {
    return null;
  }
}

export async function getTeamWeeklySummary(weekStart: string): Promise<TeamWeeklySummary[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/team/users/my-team/summary/weekly?week_start=${weekStart}`,
      {
        headers: {
          Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
        },
        cache: "no-store",
      },
    );
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as TeamWeeklySummary[];
  } catch {
    return null;
  }
}

export async function getTeamUsers(): Promise<TeamMember[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/team/users`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as TeamMember[];
  } catch {
    return null;
  }
}

export async function getLocalUsers(): Promise<LocalUser[] | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/developer/users/local`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as LocalUser[];
  } catch {
    return null;
  }
}

export async function getJournalEntries(workDate: string): Promise<JournalEntriesResponse | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/journal/entries?work_date=${workDate}`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as JournalEntriesResponse;
  } catch {
    return null;
  }
}

export async function getJournalEntryById(entryId: string): Promise<JournalEntry | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/journal/entries/${entryId}`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as JournalEntry;
  } catch {
    return null;
  }
}

export async function createJournalEntryWithBackend(payload: CreateJournalEntryPayload): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}

export async function importJournalEntriesWithBackend(payload: BulkJournalImportPayload): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/import`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}

export async function previewJournalEntriesWithBackend(payload: BulkJournalImportPayload): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/import/preview`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}

export async function importExcelJournalEntriesWithBackend(formData: FormData): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/import/excel`, {
    method: "POST",
    headers,
    body: formData,
    cache: "no-store",
  });
}

export async function previewExcelJournalEntriesWithBackend(formData: FormData): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/import/excel/preview`, {
    method: "POST",
    headers,
    body: formData,
    cache: "no-store",
  });
}

export async function deduplicateJournalEntriesWithBackend(workDate: string): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/deduplicate?work_date=${workDate}`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function deleteJournalEntriesForDateWithBackend(workDate: string): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/delete-for-date?work_date=${workDate}`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function deleteAllJournalEntriesWithBackend(): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/delete-all`, {
    method: "POST",
    headers,
    cache: "no-store",
  });
}

export async function deleteSelectedJournalEntriesWithBackend(
  payload: JournalSelectedDeletePayload,
): Promise<Response> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return new Response(JSON.stringify({ detail: "Требуется авторизация" }), {
      status: 401,
      headers: { "Content-Type": "application/json" },
    });
  }

  const cookieHeader = csrfToken
    ? `${SESSION_COOKIE_NAME}=${sessionToken}; ${CSRF_COOKIE_NAME}=${csrfToken}`
    : `${SESSION_COOKIE_NAME}=${sessionToken}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return fetch(`${API_BASE_URL}/api/v1/journal/entries/delete-selected`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}
