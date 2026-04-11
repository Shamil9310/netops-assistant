import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { CSRF_COOKIE_NAME, SESSION_COOKIE_NAME } from "@/lib/constants";

const FLASH_COOKIE_NAME = "developer_user_creation_flash";

type CreateLocalUserPayload = {
  username: string;
  full_name: string;
  password?: string;
  role: string;
  is_active: boolean;
};

type CreateLocalUserResponse = {
  generated_password?: string | null;
  user?: {
    username: string;
  };
};

function isCreateLocalUserResponse(
  value: CreateLocalUserResponse | unknown,
): value is CreateLocalUserResponse {
  return typeof value === "object" && value !== null && ("user" in value || "generated_password" in value);
}

export async function POST(request: Request) {
  const contentType = request.headers.get("content-type") ?? "";
  const isHtmlForm = contentType.includes("application/x-www-form-urlencoded")
    || contentType.includes("multipart/form-data");

  const requestPayload = await readPayload(request, isHtmlForm);

  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const csrfToken = cookieStore.get(CSRF_COOKIE_NAME)?.value;
  if (!sessionToken) {
    if (isHtmlForm) {
      return redirectTo("/login");
    }
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

  const backendResponse = await fetch(`${SERVER_API_BASE_URL}/api/v1/developer/users/local`, {
    method: "POST",
    headers,
    body: JSON.stringify(requestPayload),
    cache: "no-store",
  });

  const responseBody = (await backendResponse.json()) as CreateLocalUserResponse | unknown;
  if (!backendResponse.ok) {
    const detail = extractErrorMessage(responseBody, "Не удалось создать пользователя");

    if (isHtmlForm) {
      return redirectTo(`/developer/users?create_user_error=${encodeURIComponent(detail)}`);
    }
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }

  if (isHtmlForm) {
    const generatedPassword = isCreateLocalUserResponse(responseBody) && typeof responseBody.generated_password === "string"
      ? responseBody.generated_password
      : "";
    const createdUsername = isCreateLocalUserResponse(responseBody)
      ? responseBody.user?.username ?? ""
      : "";
    const response = redirectTo("/developer/users");
    response.cookies.set(
      FLASH_COOKIE_NAME,
      encodeURIComponent(
        JSON.stringify({
          generated_password: generatedPassword,
          created_username: createdUsername,
        }),
      ),
      {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/developer/users",
        maxAge: 60,
      },
    );
    return response;
  }
  return NextResponse.json(responseBody, { status: backendResponse.status });
}

async function readPayload(request: Request, isHtmlForm: boolean): Promise<CreateLocalUserPayload> {
  if (isHtmlForm) {
    const formData = await request.formData();
    return {
      username: String(formData.get("username") ?? ""),
      full_name: String(formData.get("full_name") ?? ""),
      password: String(formData.get("password") ?? "").trim() || undefined,
      role: String(formData.get("role") ?? "employee"),
      is_active: String(formData.get("is_active") ?? "true") === "true",
    };
  }
  return (await request.json()) as CreateLocalUserPayload;
}

function redirectTo(path: string): NextResponse {
  const response = new NextResponse(null, { status: 303 });
  response.headers.set("Location", path);
  return response;
}
