import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";
import { loginWithBackend, type LoginPayload, type LoginResponse } from "@/lib/api";

export async function POST(request: Request) {
  const contentType = request.headers.get("content-type") ?? "";
  const isHtmlForm = contentType.includes("application/x-www-form-urlencoded")
    || contentType.includes("multipart/form-data");

  const requestPayload = await readLoginPayload(request, isHtmlForm);
  const backendResponse = await loginWithBackend(requestPayload);

  const responsePayload = (await backendResponse.json()) as LoginResponse | unknown;

  if (!backendResponse.ok) {
    if (isHtmlForm) {
      return redirectTo("/login?error=1");
    }

    return NextResponse.json(
      {
        detail: extractErrorMessage(responsePayload, "Ошибка входа"),
      },
      { status: backendResponse.status },
    );
  }

  const setCookieHeaders = backendResponse.headers.getSetCookie();
  const sessionToken = extractCookieValueFromList(setCookieHeaders, SESSION_COOKIE_NAME);
  const csrfToken = extractCookieValueFromList(setCookieHeaders, CSRF_COOKIE_NAME);

  if (!sessionToken) {
    if (isHtmlForm) {
      return redirectTo("/login?error=1");
    }

    return NextResponse.json(
      { detail: "Backend не вернул сессию" },
      { status: 502 },
    );
  }

  const response = isHtmlForm
    ? redirectTo("/today")
    : NextResponse.json(responsePayload);

  response.cookies.set(SESSION_COOKIE_NAME, sessionToken, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 12,
  });

  if (csrfToken) {
    response.cookies.set(CSRF_COOKIE_NAME, csrfToken, {
      httpOnly: false,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 12,
    });
  }

  return response;
}

async function readLoginPayload(
  request: Request,
  isHtmlForm: boolean,
): Promise<LoginPayload> {
  if (isHtmlForm) {
    const formData = await request.formData();

    return {
      username: String(formData.get("username") ?? ""),
      password: String(formData.get("password") ?? ""),
    };
  }

  return (await request.json()) as LoginPayload;
}

function extractCookieValueFromList(
  setCookieHeaders: string[],
  cookieName: string,
): string | null {
  for (const header of setCookieHeaders) {
    const match = header.match(new RegExp(`${cookieName}=([^;]+)`));
    if (match) return match[1];
  }
  return null;
}

function redirectTo(path: string): NextResponse {
  const response = new NextResponse(null, { status: 303 });
  response.headers.set("Location", path);
  return response;
}
