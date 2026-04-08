import { NextResponse } from "next/server";

import { refreshReportWithBackend, type ReportPreview } from "@/lib/api";

export async function POST(request: Request) {
  const requestPayload = (await request.json()) as { report_id?: string };
  if (!requestPayload.report_id || typeof requestPayload.report_id !== "string") {
    return NextResponse.json({ detail: "report_id обязателен" }, { status: 400 });
  }

  const backendResponse = await refreshReportWithBackend(requestPayload.report_id);
  const responsePayload = (await backendResponse.json()) as ReportPreview | { detail?: string };
  if (!backendResponse.ok) {
    const detail =
      "detail" in responsePayload && responsePayload.detail
        ? responsePayload.detail
        : "Не удалось обновить отчёт";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }
  return NextResponse.json(responsePayload);
}
