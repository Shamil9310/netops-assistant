"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchJournalEntries,
  deleteJournalEntry,
} from "@/lib/client-api";

export const journalKeys = {
  all: ["journal"] as const,
  byDate: (date: string) => ["journal", date] as const,
};

export function useJournalEntries(workDate: string) {
  return useQuery({
    queryKey: journalKeys.byDate(workDate),
    queryFn: () => fetchJournalEntries(workDate),
    enabled: Boolean(workDate),
  });
}

export function useDeleteJournalEntry(workDate: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) => deleteJournalEntry(entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: journalKeys.byDate(workDate) });
    },
  });
}
