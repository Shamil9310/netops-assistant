import { cookies } from "next/headers";

import { SESSION_COOKIE_NAME } from "@/lib/constants";

export type HealthResponse = {
  status: string;
  app: string;
  environment: string;
  timestamp: string;
};

export type CurrentUser = {
  id: string;
  username: string;
  full_name: string;
  is_active: boolean;
};

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginResponse = {
  message: string;
  user: CurrentUser;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/health`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as HealthResponse;
  } catch {
    return null;
  }
}

export async function loginWithBackend(payload: LoginPayload): Promise<Response> {
  return fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
}

export async function logoutWithBackend(sessionToken: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
    method: "POST",
    headers: {
      Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
    },
    cache: "no-store",
  });
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;

  if (!sessionToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as CurrentUser;
  } catch {
    return null;
  }
}
