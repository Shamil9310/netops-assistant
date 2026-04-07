import { NextResponse } from "next/server";

import { refreshReportWithBackend, type ReportPreview } from "@/lib/api";

export async function POST(request: Request) {
  const payload = (await request.json()) as { report_id?: string };
  if (!payload.report_id || typeof payload.report_id !== "string") {
    return NextResponse.json({ detail: "report_id обязателен" }, { status: 400 });
  }

  const backendResponse = await refreshReportWithBackend(payload.report_id);
  const body = (await backendResponse.json()) as ReportPreview | { detail?: string };
  if (!backendResponse.ok) {
    const detail = "detail" in body && body.detail ? body.detail : "Не удалось обновить отчёт";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }
  return NextResponse.json(body);
}
