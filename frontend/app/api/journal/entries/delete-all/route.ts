import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  deleteAllJournalEntriesWithBackend,
  type JournalBulkDeleteResponse,
} from "@/lib/api";

export async function POST() {
  const backendResponse = await deleteAllJournalEntriesWithBackend();
  const responsePayload = (await backendResponse.json()) as JournalBulkDeleteResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось удалить все записи журнала") },
      { status: backendResponse.status },
    );
  }

  return NextResponse.json(responsePayload as JournalBulkDeleteResponse, {
    status: backendResponse.status,
  });
}
