import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/constants";
import { loginWithBackend, type LoginResponse } from "@/lib/api";

export async function POST(request: Request) {
  const payload = await request.json();
  const backendResponse = await loginWithBackend(payload);
  const body = (await backendResponse.json()) as LoginResponse | { detail?: string };

  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: ("detail" in body && body.detail) ? body.detail : "Ошибка входа" },
      { status: backendResponse.status },
    );
  }

  const setCookieHeader = backendResponse.headers.get("set-cookie");
  const sessionToken = extractCookieValue(setCookieHeader, SESSION_COOKIE_NAME);

  if (!sessionToken) {
    return NextResponse.json({ detail: "Backend не вернул сессию" }, { status: 502 });
  }

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE_NAME, sessionToken, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: 60 * 60 * 12,
  });

  return NextResponse.json(body);
}

function extractCookieValue(setCookieHeader: string | null, cookieName: string): string | null {
  if (!setCookieHeader) {
    return null;
  }

  const match = setCookieHeader.match(new RegExp(`${cookieName}=([^;]+)`));
  return match?.[1] ?? null;
}
