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

  const result = await getJournalEntries(workDate);
  if (!result) {
    return NextResponse.json(
      { work_date: workDate, total: 0, items: [] satisfies JournalEntry[] } as JournalEntriesResponse,
      { status: 200 },
    );
  }
  return NextResponse.json(result);
}

export async function POST(request: Request) {
  const payload = await request.json();
  if (!isValidCreatePayload(payload)) {
    return NextResponse.json({ detail: "Некорректный формат запроса" }, { status: 400 });
  }

  const backendResponse = await createJournalEntryWithBackend(payload);
  const body = (await backendResponse.json()) as JournalEntry | { detail?: string };
  if (!backendResponse.ok) {
    const detail = "detail" in body && body.detail ? body.detail : "Не удалось создать запись";
    return NextResponse.json({ detail }, { status: backendResponse.status });
  }
  return NextResponse.json(body, { status: 201 });
}
