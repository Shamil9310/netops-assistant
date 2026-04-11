import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  deleteSelectedJournalEntriesWithBackend,
  type JournalBulkDeleteResponse,
  type JournalSelectedDeletePayload,
} from "@/lib/api";

function isValidDeletePayload(payload: unknown): payload is JournalSelectedDeletePayload {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "entry_ids" in payload &&
    Array.isArray((payload as { entry_ids?: unknown }).entry_ids)
  );
}

export async function POST(request: Request) {
  const requestPayload = await request.json();
  if (!isValidDeletePayload(requestPayload)) {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
  }

  const backendResponse = await deleteSelectedJournalEntriesWithBackend(requestPayload);
  const responsePayload = (await backendResponse.json()) as JournalBulkDeleteResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось удалить выбранные записи") },
      { status: backendResponse.status },
    );
  }

  return NextResponse.json(responsePayload as JournalBulkDeleteResponse, {
    status: backendResponse.status,
  });
}
