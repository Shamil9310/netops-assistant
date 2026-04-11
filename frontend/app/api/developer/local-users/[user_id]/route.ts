import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

export async function POST(
  request: Request,
  context: { params: Promise<{ user_id: string }> },
) {
  const { user_id: userId } = await context.params;
  const formData = await request.formData();
  const username = String(formData.get("username") ?? "");

  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return redirectTo("/login");
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

  const backendResponse = await fetch(
    `${SERVER_API_BASE_URL}/api/v1/developer/users/local/${userId}`,
    {
      method: "DELETE",
      headers,
      cache: "no-store",
    },
  );

  if (!backendResponse.ok) {
    const errorResponse = await backendResponse.json();
    const detail = extractErrorMessage(errorResponse, "Не удалось удалить пользователя");
    return redirectTo(`/developer/users?delete_user_error=${encodeURIComponent(detail)}`);
  }

  const successUrl = new URL("/developer/users", request.url);
  successUrl.searchParams.set("delete_user_success", "1");
  if (username) {
    successUrl.searchParams.set("deleted_username", username);
  }
  return redirectTo(successUrl.pathname + successUrl.search);
}

function redirectTo(path: string): NextResponse {
  const response = new NextResponse(null, { status: 303 });
  response.headers.set("Location", path);
  return response;
}
