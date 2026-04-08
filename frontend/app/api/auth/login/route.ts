import { NextResponse } from "next/server";

import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";
import { loginWithBackend, type LoginPayload, type LoginResponse } from "@/lib/api";

type ErrorResponse = {
  detail?: string;
};

export async function POST(request: Request) {
  const content_type = request.headers.get("content-type") ?? "";
  const is_html_form = content_type.includes("application/x-www-form-urlencoded")
    || content_type.includes("multipart/form-data");

  const payload = await read_login_payload(request, is_html_form);
  const backend_response = await loginWithBackend(payload);

  const response_body = (await backend_response.json()) as LoginResponse | ErrorResponse;

  if (!backend_response.ok) {
    if (is_html_form) {
      return redirectTo("/login?error=1");
    }

    return NextResponse.json(
      {
        detail: "detail" in response_body && response_body.detail
          ? response_body.detail
          : "Ошибка входа",
      },
      { status: backend_response.status },
    );
  }

  const all_set_cookie_headers = backend_response.headers.getSetCookie();
  const session_token = extract_cookie_value_from_list(all_set_cookie_headers, SESSION_COOKIE_NAME);
  const csrf_token = extract_cookie_value_from_list(all_set_cookie_headers, CSRF_COOKIE_NAME);

  if (!session_token) {
    if (is_html_form) {
      return redirectTo("/login?error=1");
    }

    return NextResponse.json(
      { detail: "Backend не вернул сессию" },
      { status: 502 },
    );
  }

  const response = is_html_form
    ? redirectTo("/")
    : NextResponse.json(response_body);

  response.cookies.set(SESSION_COOKIE_NAME, session_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: false,
    path: "/",
    maxAge: 60 * 60 * 12,
  });

  if (csrf_token) {
    response.cookies.set(CSRF_COOKIE_NAME, csrf_token, {
      httpOnly: false,
      sameSite: "lax",
      secure: false,
      path: "/",
      maxAge: 60 * 60 * 12,
    });
  }

  return response;
}

async function read_login_payload(
  request: Request,
  is_html_form: boolean,
): Promise<LoginPayload> {
  if (is_html_form) {
    const form_data = await request.formData();

    return {
      username: String(form_data.get("username") ?? ""),
      password: String(form_data.get("password") ?? ""),
    };
  }

  return (await request.json()) as LoginPayload;
}

function extract_cookie_value_from_list(
  set_cookie_headers: string[],
  cookie_name: string,
): string | null {
  for (const header of set_cookie_headers) {
    const match = header.match(new RegExp(`${cookie_name}=([^;]+)`));
    if (match) return match[1];
  }
  return null;
}

function redirectTo(path: string): NextResponse {
  const response = new NextResponse(null, { status: 303 });
  response.headers.set("Location", path);
  return response;
}
