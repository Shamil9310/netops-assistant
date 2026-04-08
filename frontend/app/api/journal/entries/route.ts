import { NextResponse } from "next/server";

import {
  createJournalEntryWithBackend,
  getJournalEntries,
  type CreateJournalEntryPayload,
  type JournalEntriesResponse,
  type JournalEntry,
} from "@/lib/api";

function isValidCreatePayload(payload: unknown): payload is CreateJournalEntryPayload {
  if (typeof payload !== "object" || payload === null) {
    return false;
  }
  return (
    typeof (payload as { work_date?: unknown }).work_date === "string" &&
    typeof (payload as { activity_type?: unknown }).activity_type === "string" &&
    typeof (payload as { title?: unknown }).title === "string"
  );
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const workDate = url.searchParams.get("work_date");
  if (!workDate) {
    return NextResponse.json({ detail: "Параметр work_date обязателен" }, { status: 400 });
  }

  const journalEntriesResponse = await getJournalEntries(workDate);
  if (!journalEntriesResponse) {
    return NextResponse.json(
      { work_date: workDate, total: 0, items: [] satisfies JournalEntry[] } as JournalEntriesResponse,
      { status: 200 },
    );
  }
  return NextResponse.json(journalEntriesResponse);
}

export async function POST(request: Request) {
  const requestPayload = await request.json();
  if (!isValidCreatePayload(requestPayload)) {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
  }

  const backendResponse = await createJournalEntryWithBackend(requestPayload);
  const responsePayload = (await backendResponse.json()) as JournalEntry | { detail?: string };
  if (!backendResponse.ok) {
    const detail =
      "detail" in responsePayload && responsePayload.detail
        ? responsePayload.detail
        : "Не удалось создать запись";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }
  return NextResponse.json(responsePayload, { status: 201 });
}
