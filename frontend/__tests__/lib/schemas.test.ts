import { activityEntryCreateSchema } from "@/lib/schemas";

const validEntry = {
  work_date: "2024-04-12",
  activity_type: "call" as const,
  status: "open" as const,
  title: "Тестовый звонок",
};

describe("activityEntryCreateSchema", () => {
  it("принимает корректные данные", () => {
    const result = activityEntryCreateSchema.safeParse(validEntry);
    expect(result.success).toBe(true);
  });

  it("отклоняет пустой work_date", () => {
    const result = activityEntryCreateSchema.safeParse({
      ...validEntry,
      work_date: "",
    });
    expect(result.success).toBe(false);
  });

  it("отклоняет слишком короткий title", () => {
    const result = activityEntryCreateSchema.safeParse({
      ...validEntry,
      title: "ab",
    });
    expect(result.success).toBe(false);
  });

  it("отклоняет неизвестный activity_type", () => {
    const result = activityEntryCreateSchema.safeParse({
      ...validEntry,
      activity_type: "unknown",
    });
    expect(result.success).toBe(false);
  });

  it("отклоняет ended_at раньше started_at", () => {
    const result = activityEntryCreateSchema.safeParse({
      ...validEntry,
      started_at: "14:00",
      ended_at: "13:00",
    });
    expect(result.success).toBe(false);
  });

  it("принимает необязательные поля как undefined", () => {
    const result = activityEntryCreateSchema.safeParse({
      ...validEntry,
      description: undefined,
      contact: undefined,
    });
    expect(result.success).toBe(true);
  });
});
