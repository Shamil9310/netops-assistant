import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

type RoadmapSection = { module_title: string | null; topics: string[] };

type MutatePayload =
  | {
      action: "create_plan";
      title: string;
      description?: string | null;
      status?: string;
      track?: "python" | "networks";
    }
  | {
      action: "update_plan";
      plan_id: string;
      title?: string | null;
      description?: string | null;
      status?: string | null;
      track?: "python" | "networks" | null;
    }
  | { action: "delete_plan"; plan_id: string }
  | { action: "create_module"; plan_id: string; title: string; description?: string | null; order_index?: number }
  | { action: "update_module"; module_id: string; title?: string | null; description?: string | null; order_index?: number | null }
  | { action: "delete_module"; module_id: string }
  | { action: "add_checkpoint"; plan_id: string; title: string; description?: string | null; module_id?: string | null; order_index?: number }
  | { action: "bulk_add_checkpoints"; plan_id: string; sections: RoadmapSection[] }
  | { action: "update_checkpoint"; checkpoint_id: string; title?: string | null; description?: string | null; order_index?: number; is_done?: boolean | null }
  | { action: "delete_checkpoint"; checkpoint_id: string }
  | { action: "add_checklist_item"; plan_id: string; title: string; description?: string | null; checkpoint_id?: string | null; order_index?: number }
  | { action: "update_checklist_item"; item_id: string; title?: string | null; description?: string | null; checkpoint_id?: string | null; order_index?: number; is_done?: boolean | null }
  | { action: "delete_checklist_item"; item_id: string }
  | {
      action: "change_timer";
      plan_id: string;
      checkpoint_id?: string | null;
      timer_action: "start" | "pause" | "stop";
      progress_percent?: number | null;
    };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

// Преобразуем все действия интерфейса в короткие backend-запросы без дублирования логики в UI.
function buildBackendRequest(payload: MutatePayload): { path: string; method: "POST" | "PATCH" | "DELETE"; body?: object } | null {
  if (payload.action === "create_plan") {
    return {
      path: "/api/v1/study/plans",
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        track: payload.track ?? "python",
        status: payload.status ?? "draft",
      },
    };
  }
  if (payload.action === "update_plan") {
    return {
      path: `/api/v1/study/plans/${payload.plan_id}`,
      method: "PATCH",
      body: {
        title: payload.title ?? null,
        description: payload.description ?? null,
        track: payload.track ?? null,
        status: payload.status ?? null,
      },
    };
  }
  if (payload.action === "delete_plan") {
    return { path: `/api/v1/study/plans/${payload.plan_id}`, method: "DELETE" };
  }
  if (payload.action === "create_module") {
    return {
      path: `/api/v1/study/plans/${payload.plan_id}/modules`,
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        order_index: payload.order_index ?? 0,
      },
    };
  }
  if (payload.action === "update_module") {
    return {
      path: `/api/v1/study/modules/${payload.module_id}`,
      method: "PATCH",
      body: {
        title: payload.title ?? null,
        description: payload.description ?? null,
        order_index: payload.order_index ?? null,
      },
    };
  }
  if (payload.action === "delete_module") {
    return { path: `/api/v1/study/modules/${payload.module_id}`, method: "DELETE" };
  }
  if (payload.action === "bulk_add_checkpoints") {
    return {
      path: `/api/v1/study/plans/${payload.plan_id}/checkpoints/bulk`,
      method: "POST",
      body: { sections: payload.sections },
    };
  }
  if (payload.action === "add_checkpoint") {
    return {
      path: `/api/v1/study/plans/${payload.plan_id}/checkpoints`,
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        module_id: payload.module_id ?? null,
        order_index: payload.order_index ?? 0,
      },
    };
  }
  if (payload.action === "update_checkpoint") {
    return {
      path: `/api/v1/study/checkpoints/${payload.checkpoint_id}`,
      method: "PATCH",
      body: {
        title: payload.title ?? null,
        description: payload.description ?? null,
        order_index: payload.order_index ?? null,
        is_done: payload.is_done ?? null,
      },
    };
  }
  if (payload.action === "delete_checkpoint") {
    return { path: `/api/v1/study/checkpoints/${payload.checkpoint_id}`, method: "DELETE" };
  }
  if (payload.action === "add_checklist_item") {
    return {
      path: `/api/v1/study/plans/${payload.plan_id}/checklist-items`,
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        checkpoint_id: payload.checkpoint_id ?? null,
        order_index: payload.order_index ?? 0,
      },
    };
  }
  if (payload.action === "update_checklist_item") {
    return {
      path: `/api/v1/study/checklist-items/${payload.item_id}`,
      method: "PATCH",
      body: {
        title: payload.title ?? null,
        description: payload.description ?? null,
        checkpoint_id: payload.checkpoint_id ?? null,
        order_index: payload.order_index ?? null,
        is_done: payload.is_done ?? null,
      },
    };
  }
  if (payload.action === "delete_checklist_item") {
    return { path: `/api/v1/study/checklist-items/${payload.item_id}`, method: "DELETE" };
  }
  if (payload.action === "change_timer") {
    return {
      path: `/api/v1/study/plans/${payload.plan_id}/timer`,
      method: "POST",
      body: {
        action: payload.timer_action,
        checkpoint_id: payload.checkpoint_id ?? null,
        progress_percent: payload.progress_percent ?? null,
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

  // Берём сессионную cookie и CSRF-токен, чтобы запрос оставался в текущей авторизованной сессии.
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
      { detail: extractErrorMessage(responsePayload, "Не удалось обновить учёбу") },
      { status: response.status },
    );
  }
  return NextResponse.json(responsePayload, { status: response.status });
}
