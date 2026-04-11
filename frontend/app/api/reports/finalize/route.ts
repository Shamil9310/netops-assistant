import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { finalizeReportWithBackend, type ReportPreview } from "@/lib/api";

export async function POST(request: Request) {
  const requestPayload = (await request.json()) as { report_id?: string };
  if (!requestPayload.report_id || typeof requestPayload.report_id !== "string") {
    return NextResponse.json({ detail: "report_id обязателен" }, { status: 400 });
  }

  const backendResponse = await finalizeReportWithBackend(requestPayload.report_id);
  const responsePayload = (await backendResponse.json()) as ReportPreview | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось зафиксировать отчёт") },
      { status: backendResponse.status },
    );
  }
  return NextResponse.json(responsePayload);
}
