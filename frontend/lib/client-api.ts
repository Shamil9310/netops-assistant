/**
 * Клиентские функции для запросов к Next.js API-роутам.
 * Используются в хуках React Query на стороне браузера.
 */

import type { ActivityEntry } from "@/lib/api";

export type JournalEntriesResponse = ActivityEntry[];

async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail ?? `Ошибка запроса: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchJournalEntries(
  workDate: string
): Promise<JournalEntriesResponse> {
  return apiFetch<JournalEntriesResponse>(
    `/api/journal/entries?work_date=${encodeURIComponent(workDate)}`
  );
}

export async function deleteJournalEntry(entryId: string): Promise<void> {
  await apiFetch<void>(`/api/journal/entries/${encodeURIComponent(entryId)}`, {
    method: "DELETE",
  });
}

export async function fetchPlannedEvents(params?: {
  include_completed?: boolean;
}): Promise<unknown[]> {
  const query = params?.include_completed ? "?include_completed=true" : "";
  return apiFetch<unknown[]>(`/api/planned-events${query}`);
}
