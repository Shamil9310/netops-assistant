import { NextResponse } from "next/server";

import { regenerateDraftReportWithBackend, type ReportPreview } from "@/lib/api";

export async function POST(request: Request) {
  const payload = (await request.json()) as { report_id?: string };
  if (!payload.report_id || typeof payload.report_id !== "string") {
    return NextResponse.json({ detail: "report_id обязателен" }, { status: 400 });
  }

  const backendResponse = await regenerateDraftReportWithBackend(payload.report_id);
  const body = (await backendResponse.json()) as ReportPreview | { detail?: string };
  if (!backendResponse.ok) {
    const detail = "detail" in body && body.detail ? body.detail : "Не удалось пересобрать draft";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }
  return NextResponse.json(body, { status: 201 });
}
