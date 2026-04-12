/**
 * Zod-схемы валидации форм.
 *
 * Схемы описывают правила на стороне клиента, симметричные серверной валидации.
 * Это позволяет показывать ошибки пользователю до отправки запроса.
 *
 * Каждая схема максимально точно отражает ограничения соответствующей
 * Pydantic-схемы на бэкенде, чтобы фронтенд и бэкенд были согласованы.
 */

import { z } from "zod";

/** Допустимые типы активности (синхронизировано с ActivityType в backend). */
export const ACTIVITY_TYPES = [
  "call",
  "ticket",
  "meeting",
  "task",
  "escalation",
  "other",
] as const;

/** Допустимые статусы записи (синхронизировано с ActivityStatus в backend). */
export const ACTIVITY_STATUSES = [
  "open",
  "in_progress",
  "closed",
  "cancelled",
] as const;

/**
 * Схема создания записи журнала.
 *
 * Валидирует все поля формы до отправки на сервер.
 * Временны́е поля проверяются в паре: ended_at не может быть раньше started_at.
 */
export const activityEntryCreateSchema = z
  .object({
    work_date: z.string().min(1, "Рабочая дата обязательна"),
    activity_type: z.enum(ACTIVITY_TYPES, {
      error: "Выберите тип активности",
    }),
    status: z.enum(ACTIVITY_STATUSES).default("open"),
    title: z
      .string()
      .min(3, "Название должно содержать не менее 3 символов")
      .max(255, "Название не должно превышать 255 символов"),
    description: z
      .string()
      .max(5000, "Описание не должно превышать 5000 символов")
      .nullable()
      .optional(),
    resolution: z
      .string()
      .max(5000, "Резолюция не должна превышать 5000 символов")
      .nullable()
      .optional(),
    contact: z
      .string()
      .max(256, "Контакт не должен превышать 256 символов")
      .nullable()
      .optional(),
    service: z
      .string()
      .max(256, "Сервис не должен превышать 256 символов")
      .nullable()
      .optional(),
    ticket_number: z
      .string()
      .max(64, "Номер тикета не должен превышать 64 символа")
      .nullable()
      .optional(),
    task_url: z
      .string()
      .max(2048, "URL задачи не должен превышать 2048 символов")
      .url("Укажите корректный URL")
      .nullable()
      .optional()
      .or(z.literal("")),
    started_at: z
      .string()
      .regex(/^\d{2}:\d{2}$/, "Формат времени: ЧЧ:ММ")
      .nullable()
      .optional()
      .or(z.literal("")),
    ended_at: z
      .string()
      .regex(/^\d{2}:\d{2}$/, "Формат времени: ЧЧ:ММ")
      .nullable()
      .optional()
      .or(z.literal("")),
  })
  .refine(
    (data) => {
      if (data.started_at && data.ended_at) {
        return data.ended_at >= data.started_at;
      }
      return true;
    },
    {
      message: "Время окончания не может быть раньше времени начала",
      path: ["ended_at"],
    },
  );

export type ActivityEntryCreateFormData = z.infer<
  typeof activityEntryCreateSchema
>;

/**
 * Схема редактирования записи журнала.
 *
 * Все поля опциональны (частичное обновление),
 * но если переданы — проходят те же ограничения что и при создании.
 */
export const activityEntryUpdateSchema = z
  .object({
    work_date: z.string().optional(),
    activity_type: z.enum(ACTIVITY_TYPES).optional(),
    status: z.enum(ACTIVITY_STATUSES).optional(),
    title: z
      .string()
      .min(3, "Название должно содержать не менее 3 символов")
      .max(255, "Название не должно превышать 255 символов")
      .optional(),
    description: z
      .string()
      .max(5000, "Описание не должно превышать 5000 символов")
      .nullable()
      .optional(),
    resolution: z
      .string()
      .max(5000, "Резолюция не должна превышать 5000 символов")
      .nullable()
      .optional(),
    contact: z
      .string()
      .max(256, "Контакт не должен превышать 256 символов")
      .nullable()
      .optional(),
    service: z
      .string()
      .max(256, "Сервис не должен превышать 256 символов")
      .nullable()
      .optional(),
    ticket_number: z
      .string()
      .max(64, "Номер тикета не должен превышать 64 символа")
      .nullable()
      .optional(),
    task_url: z
      .string()
      .max(2048, "URL задачи не должен превышать 2048 символов")
      .url("Укажите корректный URL")
      .nullable()
      .optional()
      .or(z.literal("")),
    started_at: z
      .string()
      .regex(/^\d{2}:\d{2}$/, "Формат времени: ЧЧ:ММ")
      .nullable()
      .optional()
      .or(z.literal("")),
    ended_at: z
      .string()
      .regex(/^\d{2}:\d{2}$/, "Формат времени: ЧЧ:ММ")
      .nullable()
      .optional()
      .or(z.literal("")),
  })
  .refine(
    (data) => {
      if (data.started_at && data.ended_at) {
        return data.ended_at >= data.started_at;
      }
      return true;
    },
    {
      message: "Время окончания не может быть раньше времени начала",
      path: ["ended_at"],
    },
  );

export type ActivityEntryUpdateFormData = z.infer<
  typeof activityEntryUpdateSchema
>;

/**
 * Схема массового импорта записей журнала.
 */
export const bulkJournalImportSchema = z.object({
  text: z
    .string()
    .min(1, "Вставьте текст для импорта")
    .max(50000, "Текст не должен превышать 50 000 символов"),
  default_work_date: z.string().optional(),
});

export type BulkJournalImportFormData = z.infer<typeof bulkJournalImportSchema>;
