import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

function buildHeaders(sessionToken: string, csrfToken: string | undefined): HeadersInit {
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
  return headers;
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ entry_id: string }> },
) {
  const { entry_id: entryId } = await params;
  const requestPayload = await request.json();

  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return NextResponse.json({ detail: "Требуется авторизация" }, { status: 401 });
  }

  const response = await fetch(`${SERVER_API_BASE_URL}/api/v1/journal/entries/${entryId}`, {
    method: "PATCH",
    headers: buildHeaders(sessionToken, csrfToken),
    body: JSON.stringify(requestPayload),
    cache: "no-store",
  });

  const responsePayload = await response.json();
  if (!response.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось обновить запись") },
      { status: response.status },
    );
  }
  return NextResponse.json(responsePayload);
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ entry_id: string }> },
) {
  const { entry_id: entryId } = await params;
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return NextResponse.json({ detail: "Требуется авторизация" }, { status: 401 });
  }

  const response = await fetch(`${SERVER_API_BASE_URL}/api/v1/journal/entries/${entryId}`, {
    method: "DELETE",
    headers: buildHeaders(sessionToken, csrfToken),
    cache: "no-store",
  });

  if (!response.ok) {
    const responsePayload = await response.json();
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось удалить запись") },
      { status: response.status },
    );
  }
  return new NextResponse(null, { status: 204 });
}
