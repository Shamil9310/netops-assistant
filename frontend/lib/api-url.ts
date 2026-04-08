/**
 * Модуль для получения базового URL API в зависимости от контекста выполнения.
 *
 * Архитектурная логика:
 * - В серверном контексте (SSR, Route Handlers, Server Actions) используем INTERNAL_API_BASE_URL,
 *   чтобы Next.js ходил в backend напрямую по внутреннему адресу.
 * - В браузерном контексте используем NEXT_PUBLIC_API_BASE_URL.
 * - Для браузера fallback на localhost запрещён, чтобы не ломать работу через nginx и внешний хост.
 */

/**
 * Базовый URL для запросов из серверного контекста.
 */
export const SERVER_API_BASE_URL: string =
  process.env.INTERNAL_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

/**
 * Базовый URL для запросов из браузерного контекста.
 *
 * Пустая строка означает same-origin запросы через текущий хост,
 * под которым открыт frontend.
 */
export const CLIENT_API_BASE_URL: string =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
