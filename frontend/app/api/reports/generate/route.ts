import { NextResponse } from "next/server";

import { generateReportWithBackend, type GenerateReportPayload, type ReportPreview } from "@/lib/api";

function isValidPayload(payload: unknown): payload is GenerateReportPayload {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }

  const formatProfile = (payload as { format_profile?: unknown }).format_profile;
  if (
    formatProfile !== undefined &&
    formatProfile !== "engineer" &&
    formatProfile !== "manager"
  ) {
    return false;
  }

  const reportType = (payload as { report_type?: unknown }).report_type;
  if (reportType === "daily") {
    return typeof (payload as { report_date?: unknown }).report_date === "string";
  }
  if (reportType === "weekly") {
    return typeof (payload as { week_start?: unknown }).week_start === "string";
  }
  if (reportType === "range") {
    return (
      typeof (payload as { date_from?: unknown }).date_from === "string" &&
      typeof (payload as { date_to?: unknown }).date_to === "string"
    );
  }
  if (reportType === "night_work_result") {
    return typeof (payload as { plan_id?: unknown }).plan_id === "string";
  }
  return false;
}

export async function POST(request: Request) {
  const payload = await request.json();
  if (!isValidPayload(payload)) {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
  }

  const backendResponse = await generateReportWithBackend(payload);
  const body = (await backendResponse.json()) as ReportPreview | { detail?: string };
  if (!backendResponse.ok) {
    const detail = "detail" in body && body.detail ? body.detail : "Не удалось сгенерировать отчёт";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }

  return NextResponse.json(body, { status: 201 });
}
