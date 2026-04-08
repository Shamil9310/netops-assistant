import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { SERVER_API_BASE_URL } from "@/lib/api-url";
import { SESSION_COOKIE_NAME } from "@/lib/constants";

type TeamReportType = "daily" | "weekly" | "range";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const userId = (url.searchParams.get("user_id") ?? "").trim();
  const reportType = (url.searchParams.get("report_type") ?? "weekly").trim() as TeamReportType;

  if (!userId) {
    return redirectWithError("Не указан пользователь для выгрузки");
  }

  const backendPath = buildBackendPath(url.searchParams, userId, reportType);
  if (!backendPath) {
    return redirectWithError("Некорректные параметры выгрузки");
  }

  const cookieStore = await cookies();
  const sessionToken = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionToken) {
    return redirectWithError("Требуется авторизация");
  }

  const backendResponse = await fetch(`${SERVER_API_BASE_URL}${backendPath}`, {
    method: "GET",
    headers: {
      Cookie: `${SESSION_COOKIE_NAME}=${sessionToken}`,
    },
    cache: "no-store",
  });

  if (!backendResponse.ok) {
    const detail = await readBackendErrorDetail(backendResponse);
    return redirectWithError(detail ?? "Не удалось выгрузить отчёт");
  }

  const contentType = backendResponse.headers.get("Content-Type") ?? "text/markdown; charset=utf-8";
  const contentDisposition = backendResponse.headers.get("Content-Disposition") ?? 'attachment; filename="report.md"';
  const fileContent = await backendResponse.arrayBuffer();

  return new NextResponse(fileContent, {
    status: 200,
    headers: {
      "Content-Type": contentType,
      "Content-Disposition": contentDisposition,
    },
  });
}

function buildBackendPath(searchParams: URLSearchParams, userId: string, reportType: TeamReportType): string | null {
  if (reportType === "daily") {
    const reportDate = (searchParams.get("report_date") ?? "").trim();
    if (!reportDate) {
      return null;
    }
    return `/api/v1/team/users/${userId}/reports/daily/export/md?report_date=${encodeURIComponent(reportDate)}`;
  }

  if (reportType === "weekly") {
    const weekStart = (searchParams.get("week_start") ?? "").trim();
    if (!weekStart) {
      return null;
    }
    return `/api/v1/team/users/${userId}/reports/weekly/export/md?week_start=${encodeURIComponent(weekStart)}`;
  }

  if (reportType === "range") {
    const dateFrom = (searchParams.get("date_from") ?? "").trim();
    const dateTo = (searchParams.get("date_to") ?? "").trim();
    if (!dateFrom || !dateTo) {
      return null;
    }
    return `/api/v1/team/users/${userId}/reports/range/export/md?date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`;
  }

  return null;
}

async function readBackendErrorDetail(response: Response): Promise<string | null> {
  try {
    const errorPayload = (await response.json()) as { detail?: unknown };
    if (typeof errorPayload.detail === "string" && errorPayload.detail.trim()) {
      return errorPayload.detail;
    }
  } catch {
    return null;
  }
  return null;
}

function redirectWithError(detail: string): NextResponse {
  const response = new NextResponse(null, { status: 303 });
  response.headers.set("Location", `/reports?team_export_error=${encodeURIComponent(detail)}`);
  return response;
}
