import { NextResponse } from "next/server";

import { regenerateDraftReportWithBackend, type ReportPreview } from "@/lib/api";

export async function POST(request: Request) {
  const requestPayload = (await request.json()) as { report_id?: string };
  if (!requestPayload.report_id || typeof requestPayload.report_id !== "string") {
    return NextResponse.json({ detail: "report_id обязателен" }, { status: 400 });
  }

  const backendResponse = await regenerateDraftReportWithBackend(
    requestPayload.report_id,
  );
  const responsePayload = (await backendResponse.json()) as
    | ReportPreview
    | { detail?: string };
  if (!backendResponse.ok) {
    const detail =
      "detail" in responsePayload && responsePayload.detail
        ? responsePayload.detail
        : "Не удалось пересобрать draft";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }
  return NextResponse.json(responsePayload, { status: 201 });
}
