import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

type Payload =
  | {
    action: "create_template";
    key: string;
    name: string;
    category: string;
    description?: string;
    template_payload: Record<string, unknown>;
    is_active?: boolean;
  }
  | { action: "delete_template"; template_id: string }
  | { action: "import_defaults" };

function buildRequest(actionPayload: Payload): { path: string; method: "POST" | "DELETE"; body?: object } | null {
  if (actionPayload.action === "create_template") {
    return {
      path: "/api/v1/templates",
      method: "POST",
      body: {
        key: actionPayload.key,
        name: actionPayload.name,
        category: actionPayload.category,
        description: actionPayload.description ?? null,
        template_payload: actionPayload.template_payload,
        is_active: actionPayload.is_active ?? true,
      },
    };
  }
  if (actionPayload.action === "delete_template") {
    return {
      path: `/api/v1/templates/${actionPayload.template_id}`,
      method: "DELETE",
    };
  }
  if (actionPayload.action === "import_defaults") {
    return {
      path: "/api/v1/templates/import-defaults",
      method: "POST",
    };
  }
  return null;
}

export async function POST(request: Request) {
  const actionPayload = (await request.json()) as Payload;
  const backendRequest = buildRequest(actionPayload);
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

  const responsePayload = await response.json();
  if (!response.ok) {
    return NextResponse.json(responsePayload, { status: response.status });
  }
  return NextResponse.json(responsePayload, { status: response.status });
}
