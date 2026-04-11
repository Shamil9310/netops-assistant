import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

export async function DELETE(
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
    Cookie: cookieHeader,
  };
  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  const response = await fetch(`${SERVER_API_BASE_URL}/api/v1/planned-events/${eventId}`, {
    method: "DELETE",
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const responsePayload = await response.json();
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось удалить событие") },
      { status: response.status },
    );
  }
  return new NextResponse(null, { status: 204 });
}
