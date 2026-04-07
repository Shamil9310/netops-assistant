import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { logoutWithBackend } from "@/lib/api";
import { SESSION_COOKIE_NAME } from "@/lib/constants";

export async function POST() {
  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;

  if (sessionToken) {
    await logoutWithBackend(sessionToken);
  }

  cookieStore.delete(SESSION_COOKIE_NAME);
  return new NextResponse(null, { status: 204 });
}
