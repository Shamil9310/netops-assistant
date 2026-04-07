"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  async function handleLogout() {
    setIsLoading(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      router.push("/login");
      router.refresh();
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <button
      className="btn btn-ghost btn-sm"
      style={{ width: "100%", justifyContent: "center" }}
      type="button"
      onClick={handleLogout}
      disabled={isLoading}
    >
      {isLoading ? "Выход..." : "Выйти"}
    </button>
  );
}
