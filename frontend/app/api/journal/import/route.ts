import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  importJournalEntriesWithBackend,
  type BulkJournalImportPayload,
  type BulkJournalImportResponse,
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

  const backendResponse = await importJournalEntriesWithBackend(requestPayload);
  const responsePayload = (await backendResponse.json()) as BulkJournalImportResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось импортировать записи") },
      { status: backendResponse.status },
    );
  }
  return NextResponse.json(responsePayload as BulkJournalImportResponse, {
    status: backendResponse.status,
  });
}
