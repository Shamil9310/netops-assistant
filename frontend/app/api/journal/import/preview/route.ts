import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  previewJournalEntriesWithBackend,
  type BulkJournalImportPayload,
  type BulkJournalImportPreviewResponse,
} from "@/lib/api";

function isValidImportPayload(payload: unknown): payload is BulkJournalImportPayload {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }
  return typeof (payload as { text?: unknown }).text === "string";
}

export async function POST(request: Request) {
  const requestPayload = await request.json();
  if (!isValidImportPayload(requestPayload)) {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
  }

  const backendResponse = await previewJournalEntriesWithBackend(requestPayload);
  const responsePayload = (await backendResponse.json()) as BulkJournalImportPreviewResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось подготовить предпросмотр") },
      { status: backendResponse.status },
    );
  }
  return NextResponse.json(responsePayload as BulkJournalImportPreviewResponse, {
    status: backendResponse.status,
  });
}
