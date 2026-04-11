import { NextResponse } from "next/server";

import { extractErrorMessage } from "@/lib/api-error";
import { deduplicateJournalEntriesWithBackend } from "@/lib/api";

type DeduplicationResponse = {
  work_date: string;
  removed: number;
  duplicate_ticket_numbers: string[];
};

export async function POST(request: Request) {
  const requestUrl = new URL(request.url);
  const workDate = requestUrl.searchParams.get("work_date");
  if (!workDate) {
    return NextResponse.json({ detail: "Параметр work_date обязателен" }, { status: 400 });
  }

  const backendResponse = await deduplicateJournalEntriesWithBackend(workDate);
  const responsePayload = (await backendResponse.json()) as DeduplicationResponse | unknown;
  if (!backendResponse.ok) {
    return NextResponse.json(
      { detail: extractErrorMessage(responsePayload, "Не удалось удалить дубли") },
      { status: backendResponse.status },
    );
  }

  return NextResponse.json(responsePayload as DeduplicationResponse, {
    status: backendResponse.status,
  });
}
