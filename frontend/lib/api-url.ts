/**
 * Модуль для получения базового URL API в зависимости от контекста выполнения.
 *
 * Архитектурная логика:
 * - В Next.js существуют два контекста: серверный (SSR/Route Handlers) и браузерный (клиент).
 * - В серверном контексте нужно обращаться к backend по внутреннему адресу сети (INTERNAL_API_BASE_URL),
 *   чтобы запросы шли напрямую между контейнерами, минуя публичный интернет.
 * - В браузерном контексте доступен только NEXT_PUBLIC_API_BASE_URL — публичный адрес,
 *   доступный с машины пользователя.
 * - INTERNAL_API_BASE_URL намеренно не публичная переменная (без NEXT_PUBLIC_ префикса),
 *   поэтому браузер её никогда не видит — это правильное поведение.
 */

/**
 * Базовый URL для запросов из серверного контекста (SSR, Route Handlers, Server Actions).
 *
 * Приоритет: INTERNAL_API_BASE_URL → NEXT_PUBLIC_API_BASE_URL → fallback на localhost.
 * Fallback на localhost нужен только для локальной разработки без docker-compose.
 */
export const SERVER_API_BASE_URL: string =
    process.env.INTERNAL_API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000";

/**
 * Базовый URL для запросов из браузерного контекста (клиентские компоненты).
 *
 * Использует только NEXT_PUBLIC_API_BASE_URL — переменную, которую Next.js
 * встраивает в бандл при сборке и делает доступной в браузере.
 */
export const CLIENT_API_BASE_URL: string =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
