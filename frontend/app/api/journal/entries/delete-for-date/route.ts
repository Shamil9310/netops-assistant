import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import {
  deleteJournalEntriesForDateWithBackend,
  type JournalBulkDeleteResponse,
} from "@/lib/api";

export async function POST(request: Request) {
  const requestUrl = new URL(request.url);
  const workDate = requestUrl.searchParams.get("work_date");
  if (!workDate) {
    return NextResponse.json({ detail: "Параметр work_date обязателен" }, { status: 400 });
  }

  const backendResponse = await deleteJournalEntriesForDateWithBackend(workDate);
  const responsePayload = (await backendResponse.json()) as JournalBulkDeleteResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось очистить записи за дату") },
      { status: backendResponse.status },
    );
  }

  return NextResponse.json(responsePayload as JournalBulkDeleteResponse, {
    status: backendResponse.status,
  });
}
