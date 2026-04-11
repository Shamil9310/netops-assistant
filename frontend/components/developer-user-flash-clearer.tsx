"use client";

import { useEffect } from "react";

type Props = {
  enabled: boolean;
};

export function DeveloperUserFlashClearer({ enabled }: Props) {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    void fetch("/api/developer/local-users/flash", {
      method: "POST",
      cache: "no-store",
    });
  }, [enabled]);

  return null;
}
