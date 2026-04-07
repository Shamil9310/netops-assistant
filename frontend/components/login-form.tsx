"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("engineer");
  const [password, setPassword] = useState("engineer123");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const body = (await response.json()) as { detail?: string };
        setError(body.detail ?? "Не удалось выполнить вход");
        return;
      }

      router.push("/");
      router.refresh();
    } catch {
      setError("Не удалось подключиться к приложению");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="field">
        <span className="field-label">Логин</span>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="engineer"
          autoComplete="username"
        />
      </label>

      <label className="field">
        <span className="field-label">Пароль</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Введите пароль"
          autoComplete="current-password"
        />
      </label>

      {error && <div className="form-error">{error}</div>}

      <button className="btn btn-primary auth-submit" type="submit" disabled={isLoading}>
        {isLoading ? "Вход..." : "Войти"}
      </button>
    </form>
  );
}
