import { getCurrentWorkDateIso } from "@/lib/work-date";

describe("getCurrentWorkDateIso", () => {
  it("возвращает дату в формате YYYY-MM-DD", () => {
    const result = getCurrentWorkDateIso(new Date("2024-04-12T10:00:00Z"), "Europe/Moscow");
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("корректно конвертирует UTC в московское время", () => {
    // 2024-04-11 23:00 UTC = 2024-04-12 02:00 MSK
    const result = getCurrentWorkDateIso(
      new Date("2024-04-11T23:00:00Z"),
      "Europe/Moscow"
    );
    expect(result).toBe("2024-04-12");
  });

  it("возвращает дату по умолчанию для текущего момента", () => {
    const result = getCurrentWorkDateIso();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
