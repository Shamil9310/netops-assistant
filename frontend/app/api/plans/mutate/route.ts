import { cookies } from "next/headers";
import { NextResponse } from "next/server";

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

function buildBackendRequest(payload: MutatePayload): { path: string; method: "POST" | "PATCH"; body: object } | null {
  if (payload.action === "create_plan") {
    return {
      path: "/api/v1/plans",
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        scheduled_at: payload.scheduled_at ?? null,
        participants: payload.participants ?? [],
      },
    };
  }
  if (payload.action === "change_plan_status") {
    return {
      path: `/api/v1/plans/${payload.plan_id}/status`,
      method: "PATCH",
      body: { status: payload.status },
    };
  }
  if (payload.action === "update_plan") {
    return {
      path: `/api/v1/plans/${payload.plan_id}`,
      method: "PATCH",
      body: {
        title: payload.title ?? null,
        description: payload.description ?? null,
        scheduled_at: payload.scheduled_at ?? null,
        participants: payload.participants ?? null,
      },
    };
  }
  if (payload.action === "add_block") {
    return {
      path: `/api/v1/plans/${payload.plan_id}/blocks`,
      method: "POST",
      body: {
        title: payload.title,
        sr_number: payload.sr_number ?? null,
        description: payload.description ?? null,
        order_index: payload.order_index ?? 0,
      },
    };
  }
  if (payload.action === "change_block_status") {
    return {
      path: `/api/v1/plans/${payload.plan_id}/blocks/${payload.block_id}/status`,
      method: "PATCH",
      body: { status: payload.status, result_comment: payload.result_comment ?? null },
    };
  }
  if (payload.action === "add_step") {
    return {
      path: `/api/v1/plans/${payload.plan_id}/blocks/${payload.block_id}/steps`,
      method: "POST",
      body: {
        title: payload.title,
        description: payload.description ?? null,
        order_index: payload.order_index ?? 0,
        is_rollback: payload.is_rollback ?? false,
        is_post_action: payload.is_post_action ?? false,
      },
    };
  }
  if (payload.action === "change_step_status") {
    return {
      path: `/api/v1/plans/${payload.plan_id}/blocks/${payload.block_id}/steps/${payload.step_id}/status`,
      method: "PATCH",
      body: {
        status: payload.status,
        actual_result: payload.actual_result ?? null,
        executor_comment: payload.executor_comment ?? null,
        collaborators: payload.collaborators ?? [],
        handoff_to: payload.handoff_to ?? null,
      },
    };
  }
  if (payload.action === "create_from_template") {
    return {
      path: "/api/v1/plans/from-template",
      method: "POST",
      body: {
        template_id: payload.template_id,
        title: payload.title ?? null,
        scheduled_at: payload.scheduled_at ?? null,
        variables: payload.variables ?? {},
      },
    };
  }
  return null;
}

export async function POST(request: Request) {
  const payload = (await request.json()) as MutatePayload;
  const backendRequest = buildBackendRequest(payload);
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

  const body = await response.json();
  if (!response.ok) {
    return NextResponse.json(body, { status: response.status });
  }
  return NextResponse.json(body, { status: response.status });
}
