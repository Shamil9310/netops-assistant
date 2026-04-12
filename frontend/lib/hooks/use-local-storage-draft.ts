"use client";

import { useCallback, useEffect, useState } from "react";

type DraftUpdater<T> = T | ((current: T) => T);

export function useLocalStorageDraft<T extends Record<string, unknown>>(
  storageKey: string,
  initialValue: T,
) {
  const [draft, setDraft] = useState<T>(initialValue);
  const [isHydrated, setIsHydrated] = useState(false);
  const initialValueJson = JSON.stringify(initialValue);

  useEffect(() => {
    try {
      const rawValue = window.localStorage.getItem(storageKey);
      if (!rawValue) {
        setIsHydrated(true);
        return;
      }

      const parsedValue = JSON.parse(rawValue) as Partial<T>;
      setDraft({ ...initialValue, ...parsedValue });
    } catch {
      window.localStorage.removeItem(storageKey);
    } finally {
      setIsHydrated(true);
    }
  }, [initialValueJson, storageKey]);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }

    window.localStorage.setItem(storageKey, JSON.stringify(draft));
  }, [draft, isHydrated, storageKey]);

  const updateDraft = useCallback((nextValue: DraftUpdater<T>) => {
    setDraft((currentDraft) =>
      typeof nextValue === "function" ? nextValue(currentDraft) : nextValue,
    );
  }, []);

  const clearDraft = useCallback(() => {
    window.localStorage.removeItem(storageKey);
    setDraft(initialValue);
  }, [initialValue, storageKey]);

  return {
    draft,
    setDraft: updateDraft,
    clearDraft,
    isHydrated,
  };
}
