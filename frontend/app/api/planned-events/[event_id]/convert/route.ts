import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ event_id: string }> },
) {
  const { event_id: eventId } = await params;
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

  const response = await fetch(
    `${SERVER_API_BASE_URL}/api/v1/planned-events/${eventId}/convert-to-journal`,
    {
      method: "POST",
      headers,
      cache: "no-store",
    },
  );

  const responsePayload = await response.json();
  if (!response.ok) {
    return NextResponse.json(responsePayload, { status: response.status });
  }
  return NextResponse.json(responsePayload);
}
