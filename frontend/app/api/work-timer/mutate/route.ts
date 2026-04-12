import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

type MutatePayload =
  | {
      action: "create_task";
      title: string;
      description?: string | null;
      task_ref?: string | null;
      task_url?: string | null;
      tags?: string[];
      order_index?: number;
      status?: "todo" | "in_progress" | "done" | "cancelled";
    }
  | {
      action: "update_task";
      task_id: string;
      title?: string | null;
      description?: string | null;
      task_ref?: string | null;
      task_url?: string | null;
      tags?: string[] | null;
      order_index?: number | null;
      status?: "todo" | "in_progress" | "done" | "cancelled" | null;
      completed_at?: string | null;
    }
  | { action: "delete_task"; task_id: string }
  | {
      action: "change_timer";
      task_id: string;
      timer_action: "start" | "pause" | "resume" | "stop";
      interruption_reason?: string | null;
    };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function buildBackendRequest(
  payload: MutatePayload,
): { path: string; method: "POST" | "PATCH" | "DELETE"; body?: object } | null {
  if (payload.action === "create_task") {
    return {
      path: "/api/v1/work-timer/tasks",
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        task_ref: payload.task_ref ?? null,
        task_url: payload.task_url ?? null,
        tags: payload.tags ?? [],
        order_index: payload.order_index ?? 0,
        status: payload.status ?? "todo",
      },
    };
  }
  if (payload.action === "update_task") {
    return {
      path: `/api/v1/work-timer/tasks/${payload.task_id}`,
      method: "PATCH",
      body: {
        title: payload.title ?? null,
        description: payload.description ?? null,
        task_ref: payload.task_ref ?? null,
        task_url: payload.task_url ?? null,
        tags: payload.tags ?? null,
        order_index: payload.order_index ?? null,
        status: payload.status ?? null,
        completed_at: payload.completed_at ?? null,
      },
    };
  }
  if (payload.action === "delete_task") {
    return { path: `/api/v1/work-timer/tasks/${payload.task_id}`, method: "DELETE" };
  }
  if (payload.action === "change_timer") {
    return {
      path: `/api/v1/work-timer/tasks/${payload.task_id}/timer`,
      method: "POST",
      body: {
        action: payload.timer_action,
        interruption_reason: payload.interruption_reason ?? null,
      },
    };
  }
  return null;
}

export async function POST(request: Request) {
  const requestPayload = (await request.json()) as unknown;
  if (!isObject(requestPayload) || typeof requestPayload.action !== "string") {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
  }

  const backendRequest = buildBackendRequest(requestPayload as MutatePayload);
  if (!backendRequest) {
    return NextResponse.json({ detail: "Некорректный action" }, { status: 400 });
  }

  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return NextResponse.json({ detail: "Требуется авторизация" }, { status: 401 });
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

  const response = await fetch(`${SERVER_API_BASE_URL}${backendRequest.path}`, {
    method: backendRequest.method,
    headers,
    body: backendRequest.body ? JSON.stringify(backendRequest.body) : undefined,
    cache: "no-store",
  });

  if (response.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  const responsePayload = await response.json().catch(() => ({}));
  if (!response.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось обновить таймер") },
      { status: response.status },
    );
  }
  return NextResponse.json(responsePayload, { status: response.status });
}

