import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

type MutatePayload =
  | { action: "create_plan"; title: string; description?: string; scheduled_at?: string; participants?: string[] }
  | { action: "change_plan_status"; plan_id: string; status: string }
  | {
    action: "update_plan";
    plan_id: string;
    title?: string;
    description?: string;
    scheduled_at?: string;
    participants?: string[];
  }
  | { action: "add_block"; plan_id: string; title: string; sr_number?: string; description?: string; order_index?: number }
  | {
    action: "update_block";
    plan_id: string;
    block_id: string;
    title?: string;
    sr_number?: string;
    description?: string;
    order_index?: number;
  }
  | { action: "change_block_status"; plan_id: string; block_id: string; status: string; result_comment?: string }
  | {
    action: "add_step";
    plan_id: string;
    block_id: string;
    title: string;
    description?: string;
    order_index?: number;
    is_rollback?: boolean;
    is_post_action?: boolean;
  }
  | {
    action: "update_step";
    plan_id: string;
    block_id: string;
    step_id: string;
    title?: string;
    description?: string;
    order_index?: number;
    is_rollback?: boolean;
    is_post_action?: boolean;
  }
  | {
    action: "change_step_status";
    plan_id: string;
    block_id: string;
    step_id: string;
    status: string;
    actual_result?: string;
    executor_comment?: string;
    collaborators?: string[];
    handoff_to?: string;
  }
  | {
    action: "create_from_template";
    template_id: string;
    title?: string;
    scheduled_at?: string;
    variables?: Record<string, string>;
  };

function buildBackendRequest(actionPayload: MutatePayload): { path: string; method: "POST" | "PATCH"; body: object } | null {
  // Нормализуем все варианты действий в единый backend-запрос,
  // чтобы UI работал через один внутренний endpoint.
  if (actionPayload.action === "create_plan") {
    return {
      path: "/api/v1/plans",
      method: "POST",
      body: {
        title: actionPayload.title,
        description: actionPayload.description ?? null,
        scheduled_at: actionPayload.scheduled_at ?? null,
        participants: actionPayload.participants ?? [],
      },
    };
  }
  if (actionPayload.action === "change_plan_status") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/status`,
      method: "PATCH",
      body: { status: actionPayload.status },
    };
  }
  if (actionPayload.action === "update_plan") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}`,
      method: "PATCH",
      body: {
        title: actionPayload.title ?? null,
        description: actionPayload.description ?? null,
        scheduled_at: actionPayload.scheduled_at ?? null,
        participants: actionPayload.participants ?? null,
      },
    };
  }
  if (actionPayload.action === "add_block") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/blocks`,
      method: "POST",
      body: {
        title: actionPayload.title,
        sr_number: actionPayload.sr_number ?? null,
        description: actionPayload.description ?? null,
        order_index: actionPayload.order_index ?? 0,
      },
    };
  }
  if (actionPayload.action === "update_block") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/blocks/${actionPayload.block_id}`,
      method: "PATCH",
      body: {
        title: actionPayload.title ?? null,
        description: actionPayload.description ?? null,
        sr_number: actionPayload.sr_number ?? null,
        order_index: actionPayload.order_index ?? null,
      },
    };
  }
  if (actionPayload.action === "change_block_status") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/blocks/${actionPayload.block_id}/status`,
      method: "PATCH",
      body: { status: actionPayload.status, result_comment: actionPayload.result_comment ?? null },
    };
  }
  if (actionPayload.action === "add_step") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/blocks/${actionPayload.block_id}/steps`,
      method: "POST",
      body: {
        title: actionPayload.title,
        description: actionPayload.description ?? null,
        order_index: actionPayload.order_index ?? 0,
        is_rollback: actionPayload.is_rollback ?? false,
        is_post_action: actionPayload.is_post_action ?? false,
      },
    };
  }
  if (actionPayload.action === "update_step") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/blocks/${actionPayload.block_id}/steps/${actionPayload.step_id}`,
      method: "PATCH",
      body: {
        title: actionPayload.title ?? null,
        description: actionPayload.description ?? null,
        order_index: actionPayload.order_index ?? null,
        is_rollback: actionPayload.is_rollback ?? null,
        is_post_action: actionPayload.is_post_action ?? null,
      },
    };
  }
  if (actionPayload.action === "change_step_status") {
    return {
      path: `/api/v1/plans/${actionPayload.plan_id}/blocks/${actionPayload.block_id}/steps/${actionPayload.step_id}/status`,
      method: "PATCH",
      body: {
        status: actionPayload.status,
        actual_result: actionPayload.actual_result ?? null,
        executor_comment: actionPayload.executor_comment ?? null,
        collaborators: actionPayload.collaborators ?? [],
        handoff_to: actionPayload.handoff_to ?? null,
      },
    };
  }
  if (actionPayload.action === "create_from_template") {
    return {
      path: "/api/v1/plans/from-template",
      method: "POST",
      body: {
        template_id: actionPayload.template_id,
        title: actionPayload.title ?? null,
        scheduled_at: actionPayload.scheduled_at ?? null,
        variables: actionPayload.variables ?? {},
      },
    };
  }
  return null;
}

export async function POST(request: Request) {
  const actionPayload = (await request.json()) as MutatePayload;
  const backendRequest = buildBackendRequest(actionPayload);
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
    body: JSON.stringify(backendRequest.body),
    cache: "no-store",
  });

  if (response.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  // Возвращаем клиенту backend-ответ почти без изменений,
  // чтобы сообщения об ошибках и успешные данные не расходились.
  const responsePayload = await response.json();
  if (!response.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось изменить план") },
      { status: response.status },
    );
  }
  return NextResponse.json(responsePayload, { status: response.status });
}
