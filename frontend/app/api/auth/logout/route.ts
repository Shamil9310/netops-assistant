import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { logoutWithBackend } from "@/lib/api";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

export async function POST() {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value ?? null;

  if (sessionToken) {
    await logoutWithBackend(sessionToken, csrfToken);
  }

  cookieStore.delete(SESSION_COOKIE_NAME);
  cookieStore.delete(CSRF_COOKIE_NAME);
  return new NextResponse(null, { status: 204 });
}
