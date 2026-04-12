"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchPlannedEvents } from "@/lib/client-api";

export const plannedEventsKeys = {
  all: ["planned-events"] as const,
  filtered: (includeCompleted: boolean) =>
    ["planned-events", { includeCompleted }] as const,
};

export function usePlannedEvents(includeCompleted = false) {
  return useQuery({
    queryKey: plannedEventsKeys.filtered(includeCompleted),
    queryFn: () => fetchPlannedEvents({ include_completed: includeCompleted }),
  });
}
