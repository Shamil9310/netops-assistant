import { NextResponse } from "next/server";

const FLASH_COOKIE_NAME = "developer_user_creation_flash";

export async function POST() {
  const response = new NextResponse(null, { status: 204 });
  response.cookies.set(FLASH_COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/developer/users",
    maxAge: 0,
  });
  return response;
}
