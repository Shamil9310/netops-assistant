import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

type CreatePlannedEventPayload = {
  event_type: string;
  title: string;
  description?: string | null;
  external_ref?: string | null;
  scheduled_at: string;
};

function isValidPayload(payload: unknown): payload is CreatePlannedEventPayload {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }
  return (
    typeof (payload as { event_type?: unknown }).event_type === "string" &&
    typeof (payload as { title?: unknown }).title === "string" &&
    typeof (payload as { scheduled_at?: unknown }).scheduled_at === "string"
  );
}

export async function POST(request: Request) {
  const requestPayload = await request.json();
  if (!isValidPayload(requestPayload)) {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
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

  const response = await fetch(`${SERVER_API_BASE_URL}/api/v1/planned-events`, {
    method: "POST",
    headers,
    body: JSON.stringify(requestPayload),
    cache: "no-store",
  });

  const responsePayload = await response.json();
  if (!response.ok) {
    return NextResponse.json(responsePayload, { status: response.status });
  }
  return NextResponse.json(responsePayload, { status: 201 });
}
