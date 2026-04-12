import { formatDateLabel, formatDateTimeLabel } from "@/lib/date-format";

describe("formatDateLabel", () => {
  it("форматирует ISO дату в DD.MM.YYYY", () => {
    const result = formatDateLabel("2024-04-12");
    expect(result).toBe("12.04.2024");
  });

  it("форматирует ISO datetime, отбрасывая время", () => {
    const result = formatDateLabel("2024-04-12T10:30:00");
    expect(result).toBe("12.04.2024");
  });

  it("возвращает исходную строку при некорректной дате", () => {
    const result = formatDateLabel("not-a-date");
    expect(result).toBe("not-a-date");
  });
});

describe("formatDateTimeLabel", () => {
  it("форматирует ISO datetime в DD.MM.YYYY HH:MM", () => {
    const result = formatDateTimeLabel("2024-04-12T14:30:00");
    expect(result).toMatch(/12\.04\.2024/);
    expect(result).toMatch(/14:30/);
  });

  it("возвращает исходную строку при некорректной дате", () => {
    const result = formatDateTimeLabel("invalid");
    expect(result).toBe("invalid");
  });
});
